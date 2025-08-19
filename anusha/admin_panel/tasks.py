from celery import shared_task
import requests
from admin_panel.models import Order, Notification
from admin_panel.utils import get_shiprocket_token, send_push_notification
from django.utils import timezone
from datetime import datetime





@shared_task
def fetch_tracking_status():
    from django.db import transaction

    # ✅ Filter only orders that are in transit / not delivered
    active_orders = Order.objects.filter(
        shiprocket_awb_code__isnull=False
    ).exclude(shiprocket_awb_code='').exclude(
        shiprocket_tracking_status__in=["Delivered", "RTO Delivered", "Cancelled"]
    )

    if not active_orders.exists():
        print("ℹ️ No active orders to track")
        return

    token = get_shiprocket_token()
    headers = {"Authorization": f"Bearer {token}"}

    for order in active_orders:
        try:
            url = f"https://apiv2.shiprocket.in/v1/external/courier/track/awb/{order.shiprocket_awb_code}"
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                data = response.json()
                tracking_data = data.get("tracking_data", {})
                shipment_tracks = tracking_data.get("shipment_track", [])

                # Normalize response
                if isinstance(shipment_tracks, dict):
                    shipment_tracks = [shipment_tracks]
                elif not isinstance(shipment_tracks, list):
                    shipment_tracks = []

                if not shipment_tracks:
                    print(f"⚠️ No shipment_track data for Order #{order.id}")
                    continue

                latest_track = shipment_tracks[-1]
                current_status = latest_track.get("current_status", "")
                etd = tracking_data.get("etd", "")

                # ✅ Save only if new status
                if current_status and current_status != order.shiprocket_tracking_status:
                    with transaction.atomic():
                        order.shiprocket_tracking_status = current_status
                        order.shiprocket_tracking_info = tracking_data
                        order.shiprocket_estimated_delivery = etd
                        order.shiprocket_tracking_events = shipment_tracks
                        order.shiprocket_tracking_status_updated_at = timezone.now()
                        order.save(update_fields=[
                            "shiprocket_tracking_status",
                            "shiprocket_tracking_info",
                            "shiprocket_estimated_delivery",
                            "shiprocket_tracking_events",
                            "shiprocket_tracking_status_updated_at"
                        ])

                    # 🔔 Notify customer/admins
                    msg = f"📦 Order #{order.id} is now '{current_status}'"
                    Notification.objects.create(order=order, message=msg)
                    send_push_notification(order.user, msg)

                    print(f"✅ Order #{order.id} updated → {current_status}")
                else:
                    print(f"ℹ️ Order #{order.id} already up-to-date: {current_status}")

            elif response.status_code == 500:
                error_msg = response.json().get("message", "Unknown error")
                print(f"❌ Order #{order.id} - AWB may be cancelled: {error_msg}")
            else:
                print(f"❌ Order #{order.id} error {response.status_code}: {response.text}")

        except Exception as e:
            print(f"⚠️ Error tracking Order #{order.id}: {e}")

