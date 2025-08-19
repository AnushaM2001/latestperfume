import random
import traceback
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.utils.crypto import get_random_string
from .models import Category, Subcategory, Product, Order, OrderItem, Payment, Cart
from admin_panel.models import *
import razorpay
from django.http import HttpResponseNotAllowed, JsonResponse
from django.conf import settings
from django.views.decorators.http import require_GET
from django.http import Http404
from django.http import HttpResponse,HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from user_panel.forms import *
from user_panel.models import *
from django.contrib.auth import authenticate, login, logout,get_user_model
import string
from django.utils import timezone
from django.template.loader import render_to_string,get_template
from django.db.models import Min
from django.db.models.functions import Lower
from xhtml2pdf import pisa
from io import BytesIO
from django.core.mail import EmailMessage
from decimal import Decimal
from django.db.models import Sum
from django.db.models import Q
from django.views.decorators.http import require_POST

import redis
import json
from django.conf import settings

# Initialize Redis client
r = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB)




def a(req):
    return render(req,'user_panel/home3.html')

def generate_otp():
    return ''.join(random.choices(string.digits, k=4))


def send_otp(email, otp_code):
    subject = 'Your OTP Code'
    message = f'Your OTP code is: {otp_code}'
    from_email = settings.DEFAULT_FROM_EMAIL
    try:
        send_mail(subject, message, from_email, [email])
        print("✅ OTP sent to:", email)
    except Exception as e:
        print("❌ Email sending failed:", e)
    # send_mail(subject, message, from_email, [email])


@csrf_exempt
def send_otp_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        if email:
            otp_code = generate_otp()
            OTP.objects.create(
                email=email,
                otp=otp_code,
                expires_at=timezone.now() + timezone.timedelta(minutes=5)
            )
            send_otp(email, otp_code)
            print(otp_code)
            request.session['email'] = email
            return redirect('verify_email_otp')
    return render(request, 'user_panel/login.html')



@csrf_exempt
def verify_otp_view(request):
    email = request.session.get('email')

    if request.method == 'POST':
        if 'resend_otp' in request.POST:
            otp_code = generate_otp()
            OTP.objects.create(
                email=email,
                otp=otp_code,
                expires_at=timezone.now() + timezone.timedelta(minutes=5)
            )
            send_otp(email, otp_code)
            print("resend:", otp_code)
            return render(request, 'user_panel/verify_otp.html', {
                'email': email,
                'message': 'OTP resent successfully.'
            })

        # OTP submission
        otp = request.POST.get('otp')
        if otp:
            try:
                otp_entry = OTP.objects.filter(
                    email=email,
                    otp=otp,
                    expires_at__gte=timezone.now()
                ).latest('created_at')

                # ✅ Get or create user
                user, created = User.objects.get_or_create(username=email, defaults={'email': email})
                if not user.is_active:
                        return render(request, 'user_panel/verify_otp.html', {
                                'email': email,
                                'error': 'Your account is blocked. Please contact support.'
                            })

                # ✅ Log the user in
                login(request, user)

                request.session['emailSucessLogin'] = True
                return redirect('home')

            except OTP.DoesNotExist:
                return render(request, 'user_panel/verify_otp.html', {
                    'error': 'Invalid or expired OTP',
                    'email': email
                })

    return render(request, 'user_panel/verify_otp.html', {'email': email})

def blocked_user_view(request):
    return render(request, 'user_panel/blocked_user.html')


from django.db.models.functions import Lower
from django.db.models import Q, Min
from django.utils import timezone
from django.db.models import Min, Max
from admin_panel.models import ProductVideo

from django.http import JsonResponse
from django.core.serializers import serialize
import json

def home1(request):
    products = Product.objects.all().annotate(
    average_rating=Avg('reviews__rating'),  # average out of 5
    review_count=Count('reviews')           # total number of reviews
)
    current_time = timezone.now()
    wishlist_product_ids = []
    
    # Fetch festival offer
    festival_offer = PremiumFestiveOffer.objects.filter(
        premium_festival='Festival',
        start_date__lte=current_time,
        end_date__gt=current_time
    ).order_by('-created_at').first()

    offer_percentage = None
    startdatetime = None
    enddatetime = None
    offername = None
    if festival_offer:
        offer_percentage = festival_offer.percentage
        startdatetime = festival_offer.start_date
        enddatetime = festival_offer.end_date
        offername = festival_offer.offer_name
    else:
        print("No Festival offer found")
    print("festival offers",festival_offer)

    # Fetch banners, categories, and subcategories
    banners = Banner.objects.all().order_by('created_at')
    first_banner_no_section = None
    other_banners = []
    for banner in banners:
        if not banner.section and not first_banner_no_section:
            first_banner_no_section = banner
        else:
            other_banners.append(banner)
    categories = Category.objects.all().order_by('-created_at')[:4]
    subcategories = Subcategory.objects.annotate(
        name_lower=Lower('name')
    ).filter(
        name_lower__in=['french perfume', 'arabic perfume', 'french attar', 'arabic attar']
    ).order_by('-created_at')[:4]

    # Fetch products with min and max prices
    ScrollBar = Product.objects.filter(~Q(scroll_bar=""), ~Q(scroll_bar=None)).order_by('-created_at').first()

    best_selling = Product.objects.filter(is_best_seller=True).annotate(
    min_price=Min('variants__price'),
    max_price=Max('variants__price'),
    average_rating=Avg('reviews__rating'),      # 👈 avg rating
    review_count=Count('reviews')               # 👈 number of reviews
      ).order_by('-created_at')[:12]
    
    new_arrival = Product.objects.filter(is_new_arrival=True).annotate(
        min_price=Min('variants__price'),
        max_price=Max('variants__price'),
        average_rating=Avg('reviews__rating'),      # 👈 avg rating
    review_count=Count('reviews') 
    ).order_by('-created_at')[:12]
    trending = Product.objects.filter(is_trending=True).annotate(
        min_price=Min('variants__price'),
        max_price=Max('variants__price'),
        average_rating=Avg('reviews__rating'),      # 👈 avg rating
    review_count=Count('reviews') 
    ).order_by('-created_at')[:12]

    occasions = Subcategory.objects.annotate(
        name_lower=Lower('name')
    ).filter(
        name_lower__in=['sports', 'office', 'party', 'travel']
    ).order_by('-created_at')[:4]

    if request.user.is_authenticated:
        wishlist_product_ids = list(Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True))

    # Fetch multiple videos to display
    videos = ProductVideo.objects.all().order_by('-created_at')[:10]  # Fetch the latest 10 videos
    # Render the template with context
    return render(request, 'user_panel/home1.html', {
        'offername': offername,
        'categories': categories,
        'banners': banners,
        'subcategories': subcategories,
        'best_selling': best_selling,
        'new_arrival': new_arrival,
        'trending': trending,
        'ScrollBar': ScrollBar,
        'offer_percentage': offer_percentage,
        'startdatetime': startdatetime,
        'enddatetime': enddatetime,
        'occasions': occasions,
        'videos': videos,  # Pass multiple videos to the template
        'first_banner_no_section': first_banner_no_section,
        'wishlist_product_ids': wishlist_product_ids,
    'other_banners': other_banners,
    'festival_offer':festival_offer,
    })

##filter subcategory items ---is is shown filtered subcategories
from django.db.models import Min
from django.shortcuts import render, get_object_or_404
from admin_panel.models import ProductVideo

def video_detail(request, video_id):
    video = get_object_or_404(ProductVideo, id=video_id)
    related_products = video.related_products.all()
    return render(request, 'user_panel/video_detail.html', {
        'video': video,
        'related_products': related_products,
    })


from collections import defaultdict



def all_view(request):
    # Initialize the list of letters
    letters = list("#ABCDEFGHIJKLMNOPQRSTUVWXYZ")

    # Prepare final per-letter maps
    resolved_category_map = {}
    resolved_subcategory_map = {}

    # Initialize empty list for each letter
    for letter in letters:
        resolved_category_map[letter] = []
        resolved_subcategory_map[letter] = []

    # Fill categories
    for cat in Category.objects.all():
        first_char = cat.name[0].upper()
        key = '#' if first_char.isdigit() else first_char
        if key in resolved_category_map:
            resolved_category_map[key].append(cat)

    # Fill subcategories
    for sub in Subcategory.objects.all():
        first_char = sub.name[0].upper()
        key = '#' if first_char.isdigit() else first_char
        if key in resolved_subcategory_map:
            resolved_subcategory_map[key].append(sub)

    context = {
    'letters': letters,
    'letter_sections': [
        {
            'letter': letter,
            'categories': resolved_category_map[letter],
            'subcategories': resolved_subcategory_map[letter],
        }
        for letter in letters
    ]
}

    return render(request, 'user_panel/All.html', context)


def filtered_products(request, category_id=None, subcategory_id=None):
    category = Category.objects.filter(id=category_id).first() if category_id else None
    subcategory = Subcategory.objects.filter(id=subcategory_id).first() if subcategory_id else None

    is_giftset = category and category.name.lower().replace(' ', '').replace('-', '') == 'giftsets'
    active_offers = PremiumFestiveOffer.objects.filter(is_active=True)

    if is_giftset:
        giftsets = GiftSet.objects.filter(product__category=category).select_related('product').prefetch_related('flavours')
        for gs in giftsets:
            for offer in active_offers:
                discounted_price = offer.apply_offer(gs)  # assumes `apply_offer` works with GiftSet
                if discounted_price:
                    gs.discounted_price = discounted_price
                    gs.offer_code = offer.code
                    gs.offer_start_time = offer.start_date
                    gs.offer_end_time = offer.end_date
                    break
        products = [gs.product for gs in giftsets]
    else:
        products = Product.objects.all().annotate(price=Min('variants__price'),average_rating=Avg('reviews__rating'),
    review_count=Count('reviews'))
        if category:
            products = products.filter(category=category)
        if subcategory:
            products = products.filter(subcategory=subcategory)

        for product in products:
            for variant in product.variants.all():
                for offer in active_offers:
                    discounted_price = offer.apply_offer(variant)
                    if discounted_price:
                        variant.discounted_price = discounted_price
                        variant.offer_code = offer.code
                        variant.offer_start_time = offer.start_date
                        variant.offer_end_time = offer.end_date
                        break
    valid_prices = ProductVariant.objects.exclude(price__isnull=True).values_list('price', flat=True)
    context = {
        'category': category,
        'subcategory': subcategory,
        'categories': Category.objects.all(),
        'subcategories': Subcategory.objects.all(),
        'sizes': ProductVariant.objects.values_list('size', flat=True).distinct(),
        'min_price': int(min(valid_prices, default=0)),
        'max_price': int(max(valid_prices, default=1000)),
        'products': products,
        'product_lists': products,
        'category_banner_url': category.banner.url if category and category.banner else None,
        'subcategory_banner_url': subcategory.banner.url if subcategory and subcategory.banner else None,
        'is_giftset': is_giftset
    }

    if is_giftset:
        context['giftsets'] = giftsets

    return render(request, 'user_panel/filtered_products.html', context)

from django.db.models import Avg, Count


def ajax_filter_products(request):
    category_id = request.GET.getlist('category[]')
    subcategory_id = request.GET.getlist('subcategory[]')
    sizes = request.GET.getlist('size[]')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    active_offers = PremiumFestiveOffer.objects.filter(
        is_active=True,
        start_date__lte=timezone.now(),
        end_date__gte=timezone.now()
    )
   

    # Handle category + subcategory name/banner
    category_name = ""
    subcategory_name = ""
    category_banner_url = ""
    subcategory_banner_url = ""

    cat_obj = Category.objects.filter(id__in=category_id).first() if category_id else None
    subcat_obj = Subcategory.objects.filter(id__in=subcategory_id).first() if subcategory_id else None

    if cat_obj:
        category_name = cat_obj.name
        category_banner_url = cat_obj.banner.url if cat_obj.banner else ""

    if subcat_obj:
        subcategory_name = subcat_obj.name
        subcategory_banner_url = subcat_obj.banner.url if subcat_obj.banner else ""

    product_data = []
    

    # ✅ Handle GiftSet products
    if cat_obj and cat_obj.name.lower().replace(' ', '').replace('-', '') == 'giftsets':
        giftsets = GiftSet.objects.filter(product__category=cat_obj).select_related('product').prefetch_related('flavours')
        unique_giftproducts = {}
        for gs in giftsets:
            if gs.product.id not in unique_giftproducts:
                unique_giftproducts[gs.product.id] = gs

        for gs in unique_giftproducts.values():
            discounted_price = None
            offer_applied = None

            for offer in active_offers:
                discounted = offer.apply_offer(gs)
                if discounted:
                    discounted_price = discounted
                    offer_applied = offer
                    break

            product_data.append({
                'id': gs.product.id,
                'name': gs.product.name,
                'original_price': float(gs.price),
                'price': float(gs.price),
                'discounted_price': float(discounted_price) if discounted_price else None,
                'offer_code': offer_applied.code if offer_applied else None,
                'offer_start_time': offer_applied.start_date if offer_applied else None,
                'offer_end_time': offer_applied.end_date if offer_applied else None,
                'flavours': [f.name for f in gs.flavours.all()],
                'image': gs.product.image1.url if gs.product.image1 else '',
                'image2': gs.product.image2.url if gs.product.image2 else '',
                'is_active': gs.product.is_active,
                'is_giftset': True,
                'average_rating': float(gs.product.reviews.aggregate(avg=Avg('rating'))['avg'] or 0),
                'review_count': gs.product.reviews.count(),
                'stock_status': gs.product.stock_status or "In Stock",  # fallback if somehow null
            })

    else:
        # ✅ Handle Regular ProductVariant-based products
        variants = ProductVariant.objects.select_related('product').all()

        if category_id:
            variants = variants.filter(product__category_id__in=category_id)
        if subcategory_id:
            variants = variants.filter(product__subcategory_id__in=subcategory_id)
        if sizes:
            variants = variants.filter(size__in=sizes)
        if min_price:
            variants = variants.filter(price__gte=min_price)
        if max_price:
            variants = variants.filter(price__lte=max_price)

        unique_products = {}
        for var in variants:
            if var.product.id not in unique_products:
                unique_products[var.product.id] = var

        for var in unique_products.values():
            final_discounted_price = None
            final_offer = None

            for offer in active_offers:
                discounted = offer.apply_offer(var)
                if discounted:
                    final_discounted_price = discounted
                    final_offer = offer
                    break

            product_data.append({
                'id': var.product.id,
                'name': var.product.name,
                'original_price': var.product.original_price,
                'price': float(var.price),
                'discounted_price': float(final_discounted_price) if final_discounted_price else None,
                'offer_code': final_offer.code if final_offer else None,
                'offer_start_time': final_offer.start_date if final_offer else None,
                'offer_end_time': final_offer.end_date if final_offer else None,
                'size': var.size,
                'stock': var.stock,
                'image': var.product.image1.url if var.product.image1 else '',
                'image2': var.product.image2.url if var.product.image2 else '',
                'is_active': var.product.is_active,
                'is_giftset': False,
                'average_rating': float(var.product.reviews.aggregate(avg=Avg('rating'))['avg'] or 0),
                'review_count': var.product.reviews.count(),
                'stock_status': var.product.stock_status or "In Stock",  # fallback if somehow null
            })

    return JsonResponse({
        'products': product_data,
        'category_name': category_name,
        'subcategory_name': subcategory_name,
        'category_banner_url': category_banner_url,
        'subcategory_banner_url': subcategory_banner_url,
    })



from django.db.models import Avg

from math import floor

@login_required(login_url='email_login')
def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    reviews = Review.objects.filter(product=product).order_by('-created_at')
    review_stats = reviews.aggregate(
    avg_rating=Avg('rating'),
    total_reviews=Count('id')
)
    average_rating = review_stats['avg_rating'] or 0
    total_reviews = review_stats['total_reviews'] or 0
    rating_percentage = round((average_rating / 5) * 100, 2)
    from_video = request.GET.get('from_video')
    all_variants = product.variants.all().order_by('bottle_type')
    in_cart = Cart.objects.filter(user=request.user, product=product).exists()
    cart_item = Cart.objects.filter(user=request.user, product=product).first()

    is_giftset = product.category.name.lower().replace(' ', '').replace('-', '') == 'giftsets'
    flavours = Flavour.objects.all()
    gift_sets = GiftSet.objects.filter(product=product).select_related('product').prefetch_related('flavours')

    offers = PremiumFestiveOffer.objects.filter(is_active=True, start_date__lte=timezone.now(), end_date__gte=timezone.now())
    enhanced_reviews = []
    for r in reviews:
        enhanced_reviews.append({
        'username': r.user.username if r.user else 'Anonymous',
        'rating': r.rating,
        'review_text': r.review_text,
        'bar_width': round((r.rating / 5) * 100, 2),
    })
    
    # Apply offers to GiftSets
    gift_set_data = []
    for giftset in gift_sets:
        originalprice = giftset.price
        discounted_price = None
        applied_offer = None

        for offer in offers:
            discount = offer.apply_offer(giftset)
            if discount:
                discounted_price = discount
                applied_offer = offer
                break  # Only first matching offer

        gift_set_data.append({
            'id': giftset.id,
            'giftset': giftset,
            'price': originalprice,
            'discounted_price': discounted_price,
            'offer': {
                'name': applied_offer.offer_name,
                'percentage': applied_offer.percentage,
            } if applied_offer else None,
        })

    

    # Prepare all variants with offer & stock
    variants = []
    seen_bottle_types = set()
    unique_bottle_variants = []

    for variant in all_variants:
        if variant.bottle_type not in seen_bottle_types:
            unique_bottle_variants.append(variant)
            seen_bottle_types.add(variant.bottle_type)

        originalprice = variant.price
        stock = variant.stock
        discounted_price = None
        applied_offer = None

        for offer in offers:
            discount = offer.apply_offer(variant)
            if discount:
                discounted_price = discount
                applied_offer = offer
                break

        variants.append({
            'id': variant.id,
            'size': variant.size,
            'price': originalprice,
            'discounted_price': discounted_price,
            'stock': variant.stock,
            'in_stock': stock > 0,
            'bottle_type': variant.bottle_type,
            'offer': {
                'name': applied_offer.offer_name,
                'percentage': applied_offer.percentage,
            } if applied_offer else None
        })

    # Use first variant with discount to show on product header
    first_variant_with_offer = next((v for v in variants if v['discounted_price']), None)
    if first_variant_with_offer:
        product.discounted_price = first_variant_with_offer['discounted_price']
        product.originalprice = first_variant_with_offer['price']
        product.offer = first_variant_with_offer['offer']
    else:
        product.original_price = product.original_price
        print(product.original_price,"prrrrrrrr")
        product.offer = None

    # Related Products
   
    if product.subcategory:
        related_products = Product.objects.filter(
        subcategory=product.subcategory
    ).exclude(id=product.id)
    else:
        related_products = Product.objects.filter(
        category=product.category
    ).exclude(id=product.id)



    related_products_with_price = []
    for p in related_products:
        variant_prices = p.variants.aggregate(
        min_variant_price=Min('price'),
        max_variant_price=Max('price')
        )
            # Get min/max price from giftsets
        giftset_prices = p.gift_sets.aggregate(
        min_gift_price=Min('price'),
        max_gift_price=Max('price')
        ) 
        # Combine all prices
        all_prices = [price for price in [
        variant_prices['min_variant_price'],
        variant_prices['max_variant_price'],
        giftset_prices['min_gift_price'],
        giftset_prices['max_gift_price'],
    ] if price is not None]
        
        if all_prices:
            min_price = min(all_prices)
            max_price = max(all_prices)
            if min_price == max_price:
              price_display = f"₹{min_price}"
            else:
              price_display = f"₹{min_price} - ₹{max_price}"
        else:
            price_display = "Price not available"
        related_products_with_price.append({
        'product': p,
        'price_display': price_display,
    })
    # Best Selling Products
    

   

    return render(request, 'user_panel/product_detail.html', {
        'product': product,
        'in_cart': in_cart,
        'variants': variants,
        'cart_item': cart_item,
        'unique_bottle_variants': unique_bottle_variants,
        'related_products': related_products_with_price,
        'flavours': flavours,
        'gift_sets': gift_set_data,
        'is_giftset': is_giftset,
        'from_video':from_video,
        'reviews':reviews,
        'average_rating': average_rating,
        'rating_percentage':rating_percentage,
        'reviews': enhanced_reviews,
        'total_reviews':total_reviews


        
    })


# 🔹 Add Product to Cart

# views.py

import time  # ensure this is imported at the top

@login_required(login_url='email_login')
def add_to_cart(request, product_id):
    if not request.user.is_authenticated:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'login_required',
                'login_url': reverse('email_login'),
                'next_url': request.META.get('HTTP_REFERER') or reverse('product_detail', args=[product_id])
            }, status=401)

        next_url = request.META.get('HTTP_REFERER') or reverse('product_detail', args=[product_id])
        request.session['next_url'] = next_url
        return redirect('email_login')

    product = get_object_or_404(Product, id=product_id)

    try:
        quantity = int(request.POST.get('quantity', 1))
        action = request.POST.get('action')
        variant_id = request.POST.get('variant_id')
        gift_set_id = request.POST.get('gift_set_id')
        selected_price = request.POST.get('selected_price')

        # Redis cart key
        cart_key = f"cart:{request.user.id}"

        # Create unique item identifier
        if gift_set_id:
            item_key = f"giftset:{gift_set_id}"
            gift_set = GiftSet.objects.get(id=gift_set_id)
            price = float(selected_price) if selected_price else float(gift_set.price)
        elif variant_id:
            item_key = f"variant:{variant_id}"
            variant = ProductVariant.objects.get(id=variant_id)
            price = float(variant.price)
        else:
            item_key = f"product:{product_id}"
            price = float(product.price)

        # Get current quantity from Redis
        current_item = r.hget(cart_key, item_key)
        current_quantity = json.loads(current_item)['quantity'] if current_item else 0

        # Calculate new quantity
        if action == 'increase':
            new_quantity = current_quantity + quantity
        elif action == 'decrease':
            new_quantity = max(1, current_quantity - quantity)
        else:
            new_quantity = quantity

        # Update Redis
        item_data = {
            'product_id': product_id,
            'variant_id': variant_id,
            'gift_set_id': gift_set_id,
            'quantity': new_quantity,
            'price': price,
            'updated_at': time.time()
        }
        r.hset(cart_key, item_key, json.dumps(item_data))

        # Publish update
        r.publish(f"cart_updates:{request.user.id}", json.dumps({
            'action': 'update',
            'item_key': item_key,
            'quantity': new_quantity,
            'cart_count': r.hlen(cart_key)
        }))

        # ✅ Update database as well (dual-write)
        cart_item, created = Cart.objects.get_or_create(
            user=request.user,
            product=product,
            product_variant_id=variant_id if variant_id else None,
            gift_set_id=gift_set_id if gift_set_id else None,
            defaults={'quantity': new_quantity, 'price': price}
        )
        if not created:
            cart_item.quantity = new_quantity
            cart_item.price = price
            cart_item.save()

        # ✅ Return response
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': 'Item added to cart successfully!',
                'cart_count': r.hlen(cart_key),
                'item_id': item_key,
                'redirect_url': reverse('view_cart')
            })

        return redirect('view_cart')

    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
        messages.error(request, str(e))
        return redirect('product_detail', product_id=product_id)


# def update_cart_item(request, item_id):
#     if request.method == "POST":
        
#         try:
#             cart_item = Cart.objects.get(id=item_id, user=request.user)
#             print("Found Cart Item:", cart_item)
#         except Cart.DoesNotExist:
#             print("Cart item not found.")
#             return JsonResponse({"status": "error", "message": "CartItem not found."})

#         action = request.POST.get("action")
#         if action == "increase":
#             cart_item.quantity += 1
#         elif action == "decrease" and cart_item.quantity > 1:
#             cart_item.quantity -= 1
        
#         cart_item.save()

#         return redirect("view_cart")






# 
    
from decimal import Decimal
from django.db.models import Sum

@require_POST
@login_required
def update_cart_item(request, item_id):
    try:
        print(f"\n=== Starting update for item {item_id} ===")
        print(f"User: {request.user}")
        print(f"Action: {request.POST.get('action')}")

        # Get cart item
        cart_item = get_object_or_404(Cart, id=item_id, user=request.user)
        print(f"Current quantity: {cart_item.quantity}")

        # Update quantity
        action = request.POST.get('action')
        if action == 'increase':
            cart_item.quantity += 1
        elif action == 'decrease' and cart_item.quantity > 1:
            cart_item.quantity -= 1
        else:
            print(f"Invalid action or quantity: {action}, {cart_item.quantity}")

        cart_item.save()
        print(f"New quantity: {cart_item.quantity}")

        # Fetch all cart items
        cart_items = Cart.objects.filter(user=request.user).select_related('product')
        print(f"Total cart items: {cart_items.count()}")

        # Calculate base prices using Decimal for precision
        subtotal = sum(Decimal(item.price) * item.quantity for item in cart_items)
        delivery = sum(Decimal(item.product.delivery_charges or 0) for item in cart_items)
        platform_fee = sum(Decimal(item.product.platform_fee or 0) for item in cart_items)

        total_items = cart_items.aggregate(Sum('quantity'))['quantity__sum'] or 0
        print(f"Subtotal: {subtotal}")
        print(f"Delivery: {delivery}")
        print(f"Platform fee: {platform_fee}")

        # Get discounts and extras
        coupon_discount = Decimal(request.session.get('coupon_discount', 0))
        gift_wrap = request.session.get('gift_wrap', False)
        gift_wrap_cost = Decimal(150) if gift_wrap else Decimal(0)

        # Calculate total price
        total_price = subtotal + delivery + platform_fee - coupon_discount + gift_wrap_cost
        print(f"Coupon discount: {coupon_discount}")
        print(f"Gift wrap cost: {gift_wrap_cost}")
        print(f"Final total price: {total_price}")

        # Prepare response
        response_data = {
            'status': 'success',
            'new_quantity': cart_item.quantity,
            'cart_count': total_items,
            'item_count': total_items,
            'prices': {
                'subtotal': float(subtotal),
                'delivery': float(delivery),
                'platform_fee': float(platform_fee),
                'discount': float(coupon_discount),
                'gift_wrap': float(gift_wrap_cost),
                'total_price': float(total_price)
            }
        }

        print("=== Response Data ===")
        print(response_data)

        return JsonResponse(response_data)

    except Exception as e:
        print(f"\n!!! ERROR in update_cart_item !!!")
        print(f"Error type: {type(e)}")
        print(f"Error message: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")

        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)



from django.views.decorators.http import require_POST
from django.http import JsonResponse
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import redis
import json


import logging

logger = logging.getLogger(__name__)

@require_POST
@login_required
def remove_cart_item(request, item_id):
    try:
        # Initialize Redis
        r = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB)
        redis_key = f"cart:{request.user.id}"
        
        # Get cart item first to determine its type
        cart_item = get_object_or_404(Cart, id=item_id, user=request.user)
        
        # Use the SAME key format as in add_to_cart
        if cart_item.gift_set:
            item_key = f"giftset:{cart_item.gift_set.id}"
        elif cart_item.product_variant:
            item_key = f"variant:{cart_item.product_variant.id}"
        else:
            item_key = f"product:{cart_item.product.id}"
        
        # Delete from database FIRST
        cart_item.delete()
        
        # Then delete from Redis
        deleted = r.hdel(redis_key, item_key)
        logger.debug(f"Deleted {deleted} items from Redis")
        
        # Force immediate Redis sync
        r.save()
        
        # Get accurate count from BOTH sources
        db_items = Cart.objects.filter(user=request.user)
        db_count = db_items.count()
        db_total = db_items.aggregate(total=Sum('quantity'))['total'] or 0
        
        redis_items = r.hgetall(redis_key)
        redis_count = len(redis_items)
        redis_total = sum(
            json.loads(item_data).get('quantity', 1)
            for item_data in redis_items.values()
        ) if redis_items else 0
        
        # Final count should be from database only since we're using it as source of truth
        final_count = db_total
        
        # Clean up Redis if database is empty but Redis has items
        if db_count == 0 and redis_count > 0:
            r.delete(redis_key)
            logger.warning("Cleared Redis cart due to database mismatch")
            final_count = 0
        
        # Broadcast via WebSocket
        try:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"user_{request.user.id}_cart",
                {
                    "type": "cart.update",
                    "action": "remove",
                    "item_id": item_id,
                    "cart_count": final_count,
                    "is_empty": final_count == 0
                }
            )
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        
        return JsonResponse({
            'status': 'success',
            'message': 'Item removed successfully',
            'cart_count': final_count,
            'is_empty': final_count == 0
        })
        
    except Exception as e:
        logger.error(f"Error in remove_cart_item: {e}")
        return JsonResponse({
            'status': 'error',
            'message': str(e),
            'cart_count': 0,
            'is_empty': True
        }, status=400)

@require_GET
def cart_count(request):
    if not request.user.is_authenticated:
        return JsonResponse({'count': 0, 'status': 'unauthenticated'})

    try:
        # Use database as source of truth
        db_items = Cart.objects.filter(user=request.user)
        db_count = db_items.count()
        db_total = db_items.aggregate(total=Sum('quantity'))['total'] or 0
        
        # Edge case: items exist but quantities sum to 0
        if db_total == 0 and db_count > 0:
            db_total = db_count
        
        # Clean up Redis if out of sync
        r = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB)
        redis_key = f"cart:{request.user.id}"
        
        if db_total == 0 and r.exists(redis_key):
            r.delete(redis_key)
            logger.debug("Cleared Redis cart due to empty database")
        
        return JsonResponse({
            'count': db_total,
            'status': 'success',
            'source': 'database'  # Always use database as source of truth
        })

    except Exception as e:
        logger.error(f"Error in cart_count: {e}")
        return JsonResponse({
            'count': 0,
            'status': 'error',
            'message': str(e)
        })



def apply_coupon(request):
    if request.method == 'POST':
        coupon_code = request.POST.get('code')

        try:
            coupon = Coupon.objects.get(code=coupon_code, is_active=True)
            
            # Check if user already used it
            if CouponUsage.objects.filter(user=request.user, coupon=coupon).exists():
                messages.error(request, 'Coupon already used.')
                return redirect('view_cart')

            # Save the coupon in session
            request.session['applied_coupon'] = coupon.code
            messages.success(request, f'Coupon {coupon.discount} applied successfully!')

        except Coupon.DoesNotExist:
            messages.error(request, 'Invalid coupon code.')

    return redirect('view_cart')
from django.views.decorators.http import require_POST

@require_POST
@login_required(login_url='email_login')
def remove_coupon(request):
    # Remove applied coupon from session
    request.session.pop('applied_coupon', None)
    messages.success(request, 'Coupon removed successfully.')

    item_id = request.POST.get('item_id')
    if item_id:
        return redirect('view_cart')
    return redirect('view_cart')
from decimal import Decimal

def recalculate_cart_total(request):
    cart_items = Cart.objects.filter(user=request.user)
    total = Decimal('0.00')

    for item in cart_items:
        price = item.price or item.product_variant.price or item.product.price
        total += price * item.quantity

    delivery = sum(item.product.delivery_charges or 0 for item in cart_items)
    platform = sum(item.product.platform_fee or 0 for item in cart_items)

    premium_discount = Decimal(request.session.get('premium_offer_percentage', 0))
    premium_discount_amount = (total + delivery + platform) * premium_discount / 100 if premium_discount else Decimal('0.00')

    total_price = total + delivery + platform - premium_discount_amount
    total_price = max(total_price, Decimal('0.00'))

    return total_price, premium_discount_amount


@login_required(login_url='email_login')
def apply_premium_offer(request):
    if request.method == "POST":
        code_entered = request.POST.get('code', '').strip()
        try:
            offer = PremiumFestiveOffer.objects.get(code__iexact=code_entered)
            if PremiumOfferUsage.objects.filter(user=request.user, offer_code=offer.code).exists():
                return JsonResponse({'status': 'error', 'message': "Already used."})

            request.session['premium_offer_code'] = offer.code
            request.session['premium_offer_percentage'] = float(offer.percentage)
            PremiumOfferUsage.objects.create(user=request.user, offer_code=offer.code)

            total_price, premium_discount = recalculate_cart_total(request)

            return JsonResponse({
                'status': 'success',
                'message': f"{offer.percentage}% discount applied!",
                'total_price': str(total_price),
                'premium_discount': str(premium_discount),
            })
        except PremiumFestiveOffer.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': "Invalid code."})
    return JsonResponse({'status': 'error', 'message': "Invalid request."})


@login_required(login_url='email_login')
def remove_premium_offer(request):
    if request.method == "POST":
        code = request.session.get('premium_offer_code')
        if code:
            PremiumOfferUsage.objects.filter(user=request.user, offer_code=code).delete()
            request.session.pop('premium_offer_code', None)
            request.session.pop('premium_offer_percentage', None)
            request.session.pop(f"premium_offer_used_{code}", None)

            total_price, premium_discount = recalculate_cart_total(request)

            return JsonResponse({
                'status': 'success',
                'message': "Coupon removed.",
                'total_price': str(total_price),
                'premium_discount': str(premium_discount),
            })
        return JsonResponse({'status': 'error', 'message': "No offer to remove."})
    return JsonResponse({'status': 'error', 'message': "Invalid request."})




from django.views.decorators.http import require_POST

@require_POST
@login_required(login_url='email_login')
def toggle_gift_wrap(request):
    gift_wrap_status = request.session.get('gift_wrap', False)
    new_status = not gift_wrap_status

    # Update session
    request.session['gift_wrap'] = new_status
    request.session.modified = True

    # Update all cart items for the logged-in user
    Cart.objects.filter(user=request.user).update(gift_wrap=new_status)

    return redirect(request.META.get('HTTP_REFERER', '/'))


import hashlib
import razorpay

@login_required(login_url='email_login')
def view_cart(request):
    from_video = request.GET.get('from_video')

    all_messages = messages.get_messages(request)
    error_messages = []
    success_messages = []
    applied_successfully = False
    premium_offer_removed = False

    cart_items = Cart.objects.filter(user=request.user).order_by('-created_at')
    selected_address_id = request.session.get('selected_address_id')
  
    address = None
    if selected_address_id:
        address = AddressModel.objects.filter(id=selected_address_id, user=request.user).first()
        print("address",address)
    else:
        address = AddressModel.objects.filter(user=request.user).last()


    if not cart_items.exists():
        messages.info(request, "Your cart is currently empty.")
        return render(request, 'user_panel/cart.html', {
            'cart_items': [], 'total_price': 0, 'total_items': 0,
        })

    total_price = Decimal('0.00')
    total_items = 0
    delivery_charges = Decimal('0.00')
    platform_fee = Decimal('0.00')
    gift_wrap_display = Decimal('0.00')
    now = timezone.now()
    active_offers = PremiumFestiveOffer.objects.filter(Q(is_active=True, start_date__lte=now, end_date__gte=now)| Q(premium_festival="Welcome",
        is_active=True) | Q(premium_festival="Premium", is_active=True))

    for cart_item in cart_items:
        if cart_item.selected_flavours:
            flavour_ids = [int(fid) for fid in cart_item.selected_flavours.split(',') if fid.isdigit()]
            flavour_names = Flavour.objects.filter(id__in=flavour_ids).values_list('name', flat=True)
            cart_item.flavour_names = ', '.join(flavour_names)
        else:
            cart_item.flavour_names = ''
        product = cart_item.product
        average_rating = product.reviews.aggregate(avg=Avg('rating'))['avg'] or 0
        review_count = product.reviews.count()
        rating_percentage = (average_rating / 5) * 100  # For star fill width

    # Attach to cart_item for use in template
        cart_item.average_rating = round(average_rating, 1)
        cart_item.review_count = review_count
        cart_item.rating_percentage = rating_percentage
        variant = cart_item.product_variant
        gift_set = cart_item.gift_set if cart_item.gift_set else None
        selling_price = Decimal('0.00')
        discounted_price = None
        offer_applied = None

        if gift_set:
            selling_price = cart_item.price if cart_item.price else Decimal('0.00')
            valid_offers = [offer for offer in active_offers if offer.apply_offer(gift_set)]
            if valid_offers:
                best_offer = max(valid_offers, key=lambda x: x.percentage)
                offer_applied = best_offer
                discounted_price = selling_price
        elif variant:
            selling_price = variant.price
            valid_offers = [offer for offer in active_offers if offer.apply_offer(variant)]
            if valid_offers:
                best_offer = max(valid_offers, key=lambda x: x.percentage)
                offer_applied = best_offer
                discounted_price = selling_price - ((selling_price * best_offer.percentage) / 100)
        else:
            selling_price = product.price

        quantity = cart_item.quantity
        final_price = discounted_price if discounted_price is not None else selling_price
        total_items += quantity
        item_total = final_price * quantity
        total_price += item_total
        delivery_charges += product.delivery_charges or Decimal('0.00')
        platform_fee += product.platform_fee or Decimal('0.00')

        cart_item.final_price = final_price
        cart_item.original_price = selling_price
        cart_item.discounted_price = discounted_price
        cart_item.offer_applied = offer_applied

    if request.session.get('gift_wrap', False):
        gift_wrap_display = Decimal('150.00')

    current_cart_total = total_price + delivery_charges + platform_fee

    # Coupon
    applied_coupon_code = request.session.get('applied_coupon')
    discount = Decimal('0.00')
    applied_coupon = None
    all_coupons = Coupon.objects.filter(is_active=True)
    used_coupons = CouponUsage.objects.filter(user=request.user).values_list('coupon__id', flat=True)
    eligible_coupons = [
        coupon for coupon in all_coupons
        if coupon.required_amount <= current_cart_total and coupon.id not in used_coupons
    ]

    if applied_coupon_code:
        try:
            coupon_obj = Coupon.objects.get(code=applied_coupon_code, is_active=True)
            applied_coupon = coupon_obj
            discount = applied_coupon.discount if applied_coupon.discount else Decimal('0.00')
        except Coupon.DoesNotExist:
            request.session.pop('applied_coupon', None)

    total_price = current_cart_total + gift_wrap_display - discount

    # Premium offer
    premium_discount = Decimal('0.00')
    premium_offer_code = request.session.get('premium_offer_code')
    premium_offer_percentage = request.session.get('premium_offer_percentage')
    premium_offer_visible = False
    if premium_offer_code and premium_offer_percentage:
        try:
            premium_offer_percentage = Decimal(premium_offer_percentage)
            if premium_offer_percentage > 0:
                premium_discount = (total_price * premium_offer_percentage) / Decimal('100')
                premium_offer_visible = True
        except (ValueError, TypeError):
            pass

    total_price = current_cart_total + gift_wrap_display - premium_discount - discount
    total_price = max(total_price, Decimal('0.00'))

    # Razorpay
    cart_hash_data = f"{request.user.id}_{total_items}_{float(total_price)}"
    cart_hash = hashlib.md5(cart_hash_data.encode()).hexdigest()
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_SECRET))

    if request.session.get('razorpay_cart_hash') == cart_hash:
        razorpay_order_id = request.session.get('razorpay_order_id')
    else:
        razorpay_order = client.order.create({
            "amount": int(total_price * 100),
            "currency": "INR",
            "payment_capture": 1
        })
        razorpay_order_id = razorpay_order['id']
        request.session['razorpay_order_id'] = razorpay_order_id
        request.session['razorpay_cart_hash'] = cart_hash

    # Festival offers
    applicable_offers = []
    for offer in active_offers:
        if total_price >= getattr(offer, 'min_required', Decimal('0.00')) and offer.premium_festival == 'Welcome':
            discounted_price = (total_price * offer.percentage) / Decimal('100')
            applicable_offers.append({
                'name': offer.offer_name,
                'code': getattr(offer, 'code', ''),
                'percentage': offer.percentage,
                'discounted_price': discounted_price,
                'premium_festival': offer.premium_festival,
            })

    context = {
        'cart_items': cart_items,
        'total_price': total_price,
        'total_items': total_items,
        'address': address,
        'amount': current_cart_total,
        'delivery_charges': delivery_charges,
        'platform_fee': platform_fee,
        'discount': discount,
        'gift_wrap_display': gift_wrap_display,
        'eligible_coupons': eligible_coupons,
        'all_coupons': all_coupons,
        'used_coupons': used_coupons,
        'applied_coupon': applied_coupon,
        'razorpay_order_id': razorpay_order_id,
        'key_id': settings.RAZORPAY_KEY_ID,
        'amount_in_paise': int(total_price * 100),
        'premium_offer_code': premium_offer_code,
        'premium_discount': premium_discount,
        'error_messages': error_messages,
        'success_messages': success_messages,
        'applied_successfully': applied_successfully,
        'applicable_offers': applicable_offers,
        'premium_offer_removed': premium_offer_removed,
        'premium_offer_visible': premium_offer_visible,
        'from_video': from_video,
        'rating_percentage': rating_percentage,
        'average_rating': average_rating,
    }
    # Save applied coupon discount into session for later use
    request.session['applied_coupon_discount'] = float(discount)

    return render(request, 'user_panel/cart.html', context)


from admin_panel.utils import create_shiprocket_order,check_shiprocket_service
from admin_panel.tasks import fetch_tracking_status

from django.db import transaction
from admin_panel.views import notify_admins

@csrf_exempt
@login_required(login_url='email_login')

def order_success(request):
    if request.method == "POST":
        user = request.user
        total_price = float(request.POST.get('total_price', 0))
        razorpay_payment_id = request.POST.get('razorpay_payment_id')
        razorpay_order_id = request.POST.get('razorpay_order_id')
        razorpay_signature = request.POST.get('razorpay_signature')
        selected_address_id = request.session.get('selected_address_id')

        # Fetch address
        address = AddressModel.objects.filter(id=selected_address_id, user=user).first() if selected_address_id \
            else AddressModel.objects.filter(user=user).last()

        # Prevent duplicate order
        existing_order = Order.objects.filter(
            user=user,
            total_price=total_price,
            status="Completed",
            created_at__gte=timezone.now() - timedelta(minutes=5)
        ).first()

        if existing_order:
            order = existing_order
            print("⚠️ Using existing order to prevent duplicate:", order.id)
        else:
            try:
                # Razorpay signature verification
                client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_SECRET))
                client.utility.verify_payment_signature({
                    'razorpay_order_id': razorpay_order_id,
                    'razorpay_payment_id': razorpay_payment_id,
                    'razorpay_signature': razorpay_signature
                })

                with transaction.atomic():
                    order = Order.objects.create(
                        user=user,
                        address=address,
                        total_price=total_price,
                        status="Completed"
                    )

                    Payment.objects.create(
                        order=order,
                        payment_method="Razorpay",
                        status="Completed",
                        transaction_id=razorpay_payment_id,
                        price=total_price
                    )

                    cart_items = Cart.objects.filter(user=user)
                    # Calculate base totals for discount distribution
                    cart_total_before_discount = Decimal('0.00')
                    for item in cart_items:
                        cart_total_before_discount += item.price * item.quantity

                    coupon_discount = Decimal(request.session.get('applied_coupon_discount', 0.00))                   
                    premium_discount_percentage = Decimal(request.session.get('premium_offer_percentage', 0.00))
                    for item in cart_items:
                        quantity = item.quantity
                        original_total = item.price * quantity
                        discounted_total = item.price * quantity if item.price else original_total
                        # Product-level discount
                        product_offer_discount = original_total - discounted_total

#                         # Proportional coupon discount
                        coupon_ratio = (original_total / cart_total_before_discount) if cart_total_before_discount > 0 else Decimal('0.00')
                        coupon_discount_amount = coupon_discount * coupon_ratio

#                         # Proportional premium discount
                        premium_discount_amount = (discounted_total * premium_discount_percentage) / Decimal('100') if premium_discount_percentage > 0 else Decimal('0.00')

#                         # Total discount for this item
                        total_discount = product_offer_discount + coupon_discount_amount + premium_discount_amount


                        OrderItem.objects.create(
                            order=order,
                            product=item.product,
                            product_variant=item.product_variant,
                            quantity=item.quantity,
                            price=item.price,
                            gift_wrap=item.gift_wrap,
                            gift_set=item.gift_set,
                            offer_code=item.offer_code,
                            discount_amount=total_discount.quantize(Decimal('0.01')),

                            discount_percentage=item.discount_percentage,
                            selected_flavours=item.selected_flavours if item.selected_flavours else None
                        )
                        
                        if item.product_variant:
                            item.product_variant.stock = max(item.product_variant.stock - item.quantity, 0)
                            item.product_variant.save()
                            print(item.product_variant,"oooooooooooooooo")
                            # 🔔 Notify if stock <= 5
                            if item.product_variant.stock <= 5:
                                notify_admins(f"⚠️ Low stock for Variant: {item.product.name}-{item.product_variant.bottle_type}-{item.product_variant.size} (Stock: {item.product_variant.stock})",category="stocks")
    # ✅ Decrease stock for GiftSet
                        elif item.gift_set:
                            item.gift_set.stock = max(item.gift_set.stock - item.quantity, 0)
                            item.gift_set.save()
                            if item.gift_set.stock <= 5:
                                notify_admins(f"⚠️ Low stock for GiftSet: {item.product.name}-{item.gift_set.set_name} (Stock: {item.gift_set.stock})",category="stocks")


    # ✅ If no variant or giftset, fallback to product-level stock
                        elif item.product:
                            item.product.stock = max(item.product.stock - item.quantity, 0)
                            item.product.save()
                            if item.product.stock <= 5:
                                
                                notify_admins(f"⚠️ Low stock for Product: {item.product} (Stock: {item.product.stock})",category="stocks")


                    cart_items.delete()
                    transaction.on_commit(lambda: fetch_tracking_status.delay())

            except razorpay.errors.SignatureVerificationError:
                return render(request, 'user_panel/payment_failed.html', {"error": "Signature verification failed"})
        best_courier_data = check_shiprocket_service(user, address.id)
        if 'best_courier' in best_courier_data:
            order.shiprocket_courier_id = best_courier_data['best_courier']['courier_company_id']
            order.save(update_fields=["shiprocket_courier_id"])

        # ✅ Shiprocket order creation
        shiprocket_response = create_shiprocket_order(order, address, order.items.all())
        print("🚚 Shiprocket response:", shiprocket_response)

        if shiprocket_response.get("status") == "success":
            # Optional: Fetch tracking info immediately (if needed)
            courier_id=order.shiprocket_courier_id
            awb_code = order.shiprocket_awb_code
            if awb_code:
                tracking = fetch_shiprocket_tracking(awb_code)
                order.shiprocket_tracking_info = tracking
                order.shiprocket_tracking_status = tracking.get('current_status', '')
                order.save(update_fields=["shiprocket_tracking_info","shiprocket_tracking_status","shiprocket_courier_id"])

        # ✅ Handle coupon
        coupon_code = request.session.pop('applied_coupon', None)
        if coupon_code:
            try:
                coupon = Coupon.objects.get(code=coupon_code)
                CouponUsage.objects.create(user=user, coupon=coupon)
            except Coupon.DoesNotExist:
                pass

        # ✅ Handle premium offer usage
        premium_offer_code = request.session.pop('premium_offer_code', None)
        if premium_offer_code:
            offer = PremiumFestiveOffer.objects.filter(code=premium_offer_code).first()
            if offer:
                PremiumOfferUsage.objects.create(user=user, offer_code=offer.code)
            request.session.pop('premium_offer_percentage', None)
            request.session.pop(f'premium_offer_used_{premium_offer_code}', None)

        # ✅ Clear session keys
        for key in ['gift_wrap', 'razorpay_order_id', 'razorpay_cart_hash']:
            request.session.pop(key, None)

        messages.success(request, "Your order has been placed successfully!")
        send_invoice_email(user, order)

        return render(request, 'user_panel/order_success.html', {"order": order})

    return redirect('view_cart')










# 📝 User Registration
def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password != confirm_password:
            messages.error(request, "Passwords do not match!")
            return redirect('register')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists!")
            return redirect('register')

        user = User.objects.create_user(username=username, email=email, password=password)
        user.save()
        messages.success(request, "Account created successfully! Please log in.")
        return redirect('login')

    return render(request, 'user_panel/register.html')


def user_logout(request):
    logout(request)
    messages.success(request, "Logged out successfully!")
    return redirect('email_login')





from django.db.models import Q, Min, Max, Avg
from django.views.decorators.http import require_GET
from django.http import JsonResponse

@require_GET
def search_suggestions(request):
    query = request.GET.get('q', '').strip()
    suggestions = []

    if query:
        matching_products = Product.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query) | Q(sku__icontains=query)
        ).annotate(
            min_price=Min('variants__price'),
            max_price=Max('variants__price'),
            avg_rating=Avg('reviews__rating')  # 👈 make sure 'reviews' is the related_name in Review model
        )

        for product in matching_products:
            category_normalized = product.category.name.lower().replace(' ', '').replace('-', '')

            if category_normalized == 'giftsets':
                giftsets = GiftSet.objects.filter(product=product)
                if giftsets.exists():
                    prices = giftsets.values_list('price', flat=True)
                    if len(prices) == 1:
                        price_display = f"₹{prices[0]}"
                    else:
                        min_price = min(prices)
                        max_price = max(prices)
                        price_display = f"₹{min_price}" if min_price == max_price else f"₹{min_price} - ₹{max_price}"
                else:
                    price_display = "Price not available"
            else:
                if product.min_price and product.max_price:
                    price_display = f"₹{product.min_price}" if product.min_price == product.max_price else f"₹{product.min_price} - ₹{product.max_price}"
                else:
                    price_display = "Price not available"

            # ⭐ Round the average rating and compute fill percentage
            avg_rating = round(product.avg_rating or 0, 1)
            rating_percentage = round((avg_rating / 5) * 100, 1) if avg_rating else 0

            suggestions.append({
                'id': product.id,
                'name': product.name,
                'image': f"/media/{product.image1}" if product.image1 else '',
                'description': product.description[:100] if product.description else '',
                'url': f"/product/{product.id}/",
                'price_display': price_display,
                'average_rating': avg_rating,                # ✅ include numeric rating
                'rating_percentage': rating_percentage,      # ✅ use for stars rendering
                'original_price': product.original_price if hasattr(product, 'original_price') else None,
            })

    return JsonResponse({'results': suggestions})










@login_required(login_url='email_login')
def viewall_products(request, section):
    title = ""
    base_products = Product.objects.none()

    if section == "new-arrival":
        base_products = Product.objects.filter(is_new_arrival=True, is_active=True)
        title = "New Arrivals"
    elif section == "trending":
        base_products = Product.objects.filter(is_trending=True, is_active=True)
        title = "Trending Products"
    elif section == "best-seller":
        base_products = Product.objects.filter(is_best_seller=True, is_active=True)
        title = "Best Selling Products"
    elif section == 'shopbyocassions':
        base_products = Product.objects.filter(is_shop_by_occassion=True, is_active=True)
        title = "Shop By Occasions"

    # Annotate base products with variant price range
    base_products = base_products.annotate(
        min_price=Min('variants__price'),
        max_price=Max('variants__price'),
        average_rating=Avg('reviews__rating'),
    review_count=Count('reviews')
    )

    # Group giftsets by product and calculate min/max price per product
    giftset_prices = GiftSet.objects.filter(product__in=base_products).values('product').annotate(
        min_price=Min('price'),
        max_price=Max('price'),
    #     average_rating=Avg('reviews__rating'),
    # review_count=Count('reviews')
    )

    # Create a dictionary of product_id to giftset min/max prices
    giftset_price_map = {g['product']: g for g in giftset_prices}

    # Get product IDs that have giftsets
    giftset_product_ids = set(giftset_price_map.keys())

    # Wishlist logic
    wishlist_product_ids = []
    if request.user.is_authenticated:
        wishlist_product_ids = list(Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True))

    combined_items = []

    for product in base_products:
        is_in_wishlist = product.id in wishlist_product_ids
        average_rating = product.reviews.aggregate(avg=Avg('rating'))['avg'] or 0
        review_count = product.reviews.count()
        if product.id in giftset_product_ids:
            price_data = giftset_price_map[product.id]
            combined_items.append({
                'type': 'giftset',
                'product': product,
                'min_price': price_data['min_price'],
                'max_price': price_data['max_price'],
                'is_in_wishlist': is_in_wishlist,
        #         'average_rating': product.average_rating or 0,
                'average_rating': round(average_rating, 1),
                'review_count': review_count
            })
        else:
            combined_items.append({
                'type': 'product',
                'product': product,
                'min_price': product.min_price,
                'max_price': product.max_price,
                'is_in_wishlist': is_in_wishlist,
                'average_rating': product.average_rating or 0,
        'average_rating': round(average_rating, 1),
            'review_count': review_count
            })

    banner = Banner.objects.filter(section=section).first()

    return render(request, 'user_panel/best_products.html', {
        'combined_items': combined_items,
        'title': title,
        'banner': banner,
        'wishlist_product_ids': wishlist_product_ids,
        
    })










def user_address(request):
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()
            
            # Save selected address ID for both billing and shipping
            request.session['selected_address_id'] = address.id
            request.session['billing_address_id'] = address.id
            request.session['shipping_address_id'] = address.id

            messages.success(request, "Address saved successfully!")
            return redirect('view_cart')
        else:
            print('jjjjjjj',form.errors)
    else:
        form = AddressForm()

    return render(request, 'user_panel/add_address.html', {'form': form})

def update_address(request, address_id):
    # item_id = request.GET.get('item_id')  

    try:
        address = AddressModel.objects.get(id=address_id, user=request.user)  # Get the address to update
    except AddressModel.DoesNotExist:
        # Handle case where address doesn't exist
        return HttpResponse('No Adreess Found')  
    
    if request.method == 'POST':
        if 'reset' in request.POST:
            form = AddressForm()
        form = AddressForm(request.POST, instance=address)  
        if form.is_valid():
            form.save()  
            request.session['selected_address_id'] = address.id  # or updated_address.id
            messages.success(request, "Address updated successfully!")

            return redirect('view_cart')  # Redirect back to the cart page
        else:
            print(form.errors)
    else:
        form = AddressForm(instance=address)  

    return render(request, 'user_panel/add_address.html', {'form': form,})

    
    
#user_profile views
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import time

# @login_required(login_url='email_login')(login_url='email_login')(login_url='email_login')(login_url='email_login')(login_url='email_login')(login_url='email_login')
# def user_profile(request):
#     user = request.user
#     profile, _ = UserProfile.objects.get_or_create(user=user)

#     orders = Order.objects.filter(user=user).order_by('-created_at').prefetch_related('items')
#     wishlist = Wishlist.objects.filter(user=user).select_related('product')
#     addresses = AddressModel.objects.filter(user=user)
#     help_queries = HelpQuery.objects.filter(user=user).order_by('-created_at')

#     default_address = addresses.first()

#     # Calculate total price for each order
#     for order in orders:
#         item = order.items.first()
#         if item and item.product_variant:
#             order.calculated_total_price = item.quantity * item.product_variant.price
#         else:
#             order.calculated_total_price = None
#         if not order.shiprocket_tracking_events or not isinstance(order.shiprocket_tracking_events, list):
#             order.shiprocket_tracking_events = []

#         # ✅ Parse shiprocket_tracking_info if string
#         if order.shiprocket_tracking_info and isinstance(order.shiprocket_tracking_info, str):
#             try:
#                 order.shiprocket_tracking_info = json.loads(order.shiprocket_tracking_info)
#             except json.JSONDecodeError:
#                 order.shiprocket_tracking_info = {}

#         # ✅ Parse shiprocket_tracking_events if string
#         if order.shiprocket_tracking_events and isinstance(order.shiprocket_tracking_events, str):
#             try:
#                 order.shiprocket_tracking_events = json.loads(order.shiprocket_tracking_events)
#             except json.JSONDecodeError:
#                 order.shiprocket_tracking_events = []

#     # ✅ Get average rating per product
#     ordered_product_ids = OrderItem.objects.filter(order__user=user).values_list('product_id', flat=True)
#     product_reviews = Review.objects.filter(product_id__in=ordered_product_ids)

#     avg_rating_dict = {
#         item['product_id']: {
#             'rating': round(item['avg_rating'], 1),
#             'percentage': round((item['avg_rating'] / 5) * 100, 2)
#         }
#         for item in product_reviews.values('product_id').annotate(avg_rating=Avg('rating'))
#     }

#     reviewed_product_ids = list(
#         product_reviews.filter(user=user).values_list('product_id', flat=True)
#     )
#     tracking_stages = ["AWB Assigned", "Pickup Generated", "Out for Delivery", "Delivered"]

#     # ✅ Handle profile form
#     if request.method == 'POST':
#         form = UserProfileForm(request.POST, request.FILES, instance=profile)
#         if form.is_valid():
#             form.save()
#             messages.success(request, "Profile updated successfully!")
#             return redirect('user_profile')
#     else:
#         form = UserProfileForm(instance=profile)
    

#     return render(request, 'user_panel/user_profile2.html', {
#         'profile': profile,
#         'user': user,
#         'orders': orders,
#         'wishlist': wishlist,
#         'addresses': addresses,
#         'help_queries': help_queries,
#         'form': form,
#         'avg_rating_dict': avg_rating_dict,
#         'reviewed_product_ids': reviewed_product_ids,
#         'tracking_stages':tracking_stages
#     })if isinstance(order.shiprocket_tracking_info, dict):

@login_required(login_url='email_login')
def user_profile(request):
    user = request.user
    profile, _ = UserProfile.objects.get_or_create(user=user)

    orders = (
        Order.objects
        .filter(user=user)
        .order_by('-created_at')
        .prefetch_related('items__product', 'items__product_variant')  # Prefetch nested items
    )
    for order in orders:
        for item in order.items.all():
            if item.selected_flavours:
               flavour_ids = [int(fid) for fid in item.selected_flavours.split(',') if fid.isdigit()]
               flavours_qs = Flavour.objects.filter(id__in=flavour_ids)
               item.flavour_names = ', '.join(f.name for f in flavours_qs)
            else:
               item.flavour_names = ''
    wishlist = Wishlist.objects.filter(user=user).select_related('product')
    addresses = AddressModel.objects.filter(user=user)
    help_queries = HelpQuery.objects.filter(user=user).order_by('-created_at')

    default_address = addresses.first()

    for order in orders:
        if not order.shiprocket_tracking_events or not isinstance(order.shiprocket_tracking_events, list):
            order.shiprocket_tracking_events = []

        if order.shiprocket_tracking_info and isinstance(order.shiprocket_tracking_info, str):
            try:
                order.shiprocket_tracking_info = json.loads(order.shiprocket_tracking_info)
            except json.JSONDecodeError:
                order.shiprocket_tracking_info = {}

        if order.shiprocket_tracking_events and isinstance(order.shiprocket_tracking_events, str):
            try:
                order.shiprocket_tracking_events = json.loads(order.shiprocket_tracking_events)
            except json.JSONDecodeError:
                order.shiprocket_tracking_events = []
        if isinstance(order.shiprocket_tracking_info, dict):
            order.shipment_activities = order.shiprocket_tracking_info.get('shipment_track_activities', [])
            order.tracking_url = f"https://shiprocket.co/tracking/{order.shiprocket_awb_code}" if order.shiprocket_awb_code else None

        else:
            order.shipment_activities = []
            order.tracking_url = None

    ordered_product_ids = OrderItem.objects.filter(order__user=user).values_list('product_id', flat=True)
    product_reviews = Review.objects.filter(product_id__in=ordered_product_ids)

    avg_rating_dict = {
        item['product_id']: {
            'rating': round(item['avg_rating'], 1),
            'percentage': round((item['avg_rating'] / 5) * 100, 2)
        }
        for item in product_reviews.values('product_id').annotate(avg_rating=Avg('rating'))
    }

    reviewed_product_ids = list(
        product_reviews.filter(user=user).values_list('product_id', flat=True)
    )

    tracking_stages = ["AWB Assigned", "Pickup Generated", "Out for Pickup", "Delivered"]

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('user_profile')
    else:
        form = UserProfileForm(instance=profile)

    return render(request, 'user_panel/user_profile2.html', {
        'profile': profile,
        'user': user,
        'orders': orders,
        'wishlist': wishlist,
        'addresses': addresses,
        'help_queries': help_queries,
        'form': form,
        'avg_rating_dict': avg_rating_dict,
        'reviewed_product_ids': reviewed_product_ids,
        'tracking_stages': tracking_stages,
    })


@login_required(login_url='email_login')
def add_address(request):
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()
            messages.success(request, "Address added successfully!")
            next_url = request.POST.get('next')
            if next_url:
                return redirect(next_url) 
            return redirect('view_cart')
    else:
        form = AddressForm()
    return render(request, 'user_panel/add_address.html', {'form': form})

@login_required(login_url='email_login')
def edit_address(request, address_id):
    address = get_object_or_404(AddressModel, id=address_id, user=request.user)
    if request.method == 'POST':
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            messages.success(request, "Address updated successfully!")
            return redirect('user_profile')
    else:
        form = AddressForm(instance=address)
    return render(request, 'user_panel/edit_address.html', {'form': form, 'address': address})

@login_required(login_url='email_login')
def delete_address(request, address_id):
    address = get_object_or_404(AddressModel, id=address_id, user=request.user)
    if request.method == 'POST':
        address.delete()
        messages.success(request, "Address deleted successfully!")
        return redirect('user_profile')
    return render(request, 'user_panel/confirm_delete.html', {'address': address})

@login_required(login_url='email_login')
def submit_help_query(request):
    if request.method == 'POST':
        form = HelpQueryForm(request.POST)
        if form.is_valid():
            query = form.save(commit=False)
            query.user = request.user
            query.save()
            messages.success(request, "Your query has been submitted successfully!")
            notify_admins(f"A new query has been submitted by {query.user.email}. Query: {query.query_text}",category='queries')
            return redirect('user_profile')
    else:
        form = HelpQueryForm()
    return render(request, 'user_panel/submit_query.html', {'form': form})

@login_required(login_url='email_login')
def view_help_query(request, query_id):
    query = get_object_or_404(HelpQuery, id=query_id, user=request.user)

    # Extract admin reply if present
    admin_reply = None
    if "[Admin Reply" in query.message:
        parts = query.message.split("[Admin Reply")
        user_message = parts[0].strip()
        admin_reply = "[Admin Reply" + parts[1]
    else:
        user_message = query.message

    return render(request, 'user_panel/view_query.html', {
        'query': query,
        'user_message': user_message,
        'admin_reply': query.admin_reply
    })


from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.utils.timezone import now
from django.contrib.auth.decorators import login_required
from django.apps import apps

@login_required(login_url='email_login')
def send_help_query_message(request, query_id):
    query = get_object_or_404(HelpQuery, id=query_id, user=request.user)
    if request.method == 'POST':
        text = request.POST.get('message', '').strip()
        if not text:
            messages.error(request, "Cannot send empty message.")
            return redirect(request.META.get('HTTP_REFERER', '/'))

        # Try to save to HelpQueryMessage if the model exists; otherwise fallback to appending text to query.message
        HelpQueryMessage = None
        try:
            HelpQueryMessage = apps.get_model('user_panel', 'HelpQueryMessage')
        except LookupError:
            HelpQueryMessage = None

        if HelpQueryMessage:
            HelpQueryMessage.objects.create(query=query, sender='User', text=text)
        else:
            # fallback - append to original message (legacy)
            query.message = (query.message or '') + f"\n\n[User Reply on {now().strftime('%d-%m-%Y %H:%M')}]: {text}"
        # update status and save
        query.status = 'In Progress'
        query.save()

        messages.success(request, "Message sent.")
        # Redirect back to help center and auto-open this chat
        return redirect(f"{request.META.get('HTTP_REFERER', '/')}?open={query.id}")
    return redirect('help_center')


import os
import uuid

@csrf_exempt
@login_required(login_url='email_login')
def update_profile_picture(request):
    if request.method == 'POST':
        try:
            profile = UserProfile.objects.get(user=request.user)
            
            if 'profile_image' not in request.FILES:
                return JsonResponse({'success': False, 'error': 'No image provided'})
            
            uploaded_file = request.FILES['profile_image']
            
            # Delete old image if exists
            if profile.profile_image:
                try:
                    os.remove(profile.profile_image.path)
                except Exception as e:
                    print(f"Error deleting old image: {e}")
            
            # Generate unique filename with timestamp
            ext = uploaded_file.name.split('.')[-1]
            filename = f"{request.user.username}_{uuid.uuid4().hex[:8]}_{int(time.time())}.{ext}"
            
            # Save new image
            profile.profile_image.save(filename, uploaded_file)
            profile.save()
            
            # Return the new image URL with cache busting
            return JsonResponse({
                'success': True,
                'image_url': profile.profile_image.url,
                'timestamp': int(time.time())  # Add timestamp for cache busting
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required(login_url='email_login')
def product_list(request):
    products = Product.objects.all()
    wishlist_product_ids = Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True)
    return render(request, 'home3.html', {
        'products': products,
        'wishlist_product_ids': list(wishlist_product_ids)
    })



@require_POST
@login_required(login_url='email_login')
def add_to_wishlist(request):
    product_id = request.POST.get('product_id')
    product = Product.objects.get(id=product_id)
    Wishlist.objects.get_or_create(user=request.user, product=product)
    return JsonResponse({'success': True})

@require_POST
@login_required(login_url='email_login')
def remove_from_wishlist(request):
    product_id = request.POST.get('product_id')
    product = Product.objects.get(id=product_id)
    Wishlist.objects.filter(user=request.user, product=product).delete()
    return JsonResponse({'success': True})


@csrf_exempt
@login_required(login_url='email_login')
def update_dob(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        dob_str = data.get('dob')
        try:
            dob = datetime.strptime(dob_str, "%d-%m-%Y").date()
            profile = UserProfile.objects.get(user=request.user)
            profile.dob = dob
            profile.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid method'})

#shipping ===================================
from admin_panel.models import Order, OrderItem  # update if your models are named differently
from admin_panel.utils import fetch_shiprocket_tracking,get_shiprocket_token
def shiprocket_order_result_view(request):
    # Example: assume latest order by logged-in user
    try:
        user = request.user
        order = Order.objects.filter(user=user).latest('created_at')  # adjust field if needed
        address = AddressModel.objects.filter(user=user).latest('created_at')  # Or order.address if you store it
        order_items = OrderItem.objects.filter(order=order)

        result = create_shiprocket_order(order, address, order_items)
        return render(request, 'user_panel/home.html', {'result': result})

    except Order.DoesNotExist:
        return render(request, 'user_panel/home.html', {
            'result': {
                'status': 'error',
                'status_code': 404,
                'shiprocket_response': {'message': 'No order found for this user.'},
                'sent_payload': {}
            }
        })








@login_required(login_url='email_login')
def order_tracking_view(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    tracking = order.shiprocket_tracking_info
    print(tracking,"tracking")

    if isinstance(tracking, str):
        try:
            tracking = json.loads(tracking)
        except json.JSONDecodeError:
            tracking = {}

    shipment_tracks = tracking.get("shipment_tracks") or tracking.get("shipment_track") or []

    # if not shipment_tracks:
    #    error = "Tracking information not available yet."
    #    return render(request, 'user_panel/tracking.html', {'order': order, 'error': error})


    # Safely extract first track
    first_track = shipment_tracks[0] if shipment_tracks else {}
    shipment_activities = tracking.get("shipment_track_activities", [])

    tracking_stages = [
        "Order Confirmed",
        "AWB Assigned",
        "Pickup Generated",
        "In Transit",
        "REACHED AT DESTINATION HUB",
        "Delivered",
        # "Pick up Exception",
        # "Canceled"

    ]

    current_status = first_track.get("current_status", "")
    current_stage_index = tracking_stages.index(current_status) if current_status in tracking_stages else -1

    return render(request, 'user_panel/tracking.html', {
        'order': order,
        'courier': first_track.get('courier_name', ''),
        'awb_code': first_track.get('awb_code', ''),
        'current_status': current_status,
        'origin': first_track.get('origin', ''),
        'destination': first_track.get('destination', ''),
        'est_delivery': tracking.get('etd', '')[:10],
        'track_url': tracking.get('track_url', ''),
        'history': shipment_tracks,
        'tracking_stages': tracking_stages,
        'current_stage_index': current_stage_index,
        'shipment_activities': shipment_activities,
    })





@login_required(login_url='email_login')
def download_invoice(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    token = get_shiprocket_token()
    url = "https://apiv2.shiprocket.in/v1/external/orders/print/invoice"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "ids": [order.shiprocket_order_id]
    }

    response = requests.post(url, json=payload, headers=headers)
    data = response.json()
    if response.status_code == 200 and data.get("invoice_url"):
        return HttpResponseRedirect(data["invoice_url"])
    return JsonResponse(data, status=response.status_code)


def send_invoice_email(user, order):
    token = get_shiprocket_token()
    url = "https://apiv2.shiprocket.in/v1/external/orders/print/invoice"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "ids": [order.shiprocket_order_id]
    }

    response = requests.post(url, json=payload, headers=headers)
    data = response.json()

    if response.status_code == 200 and data.get("invoice_url"):
        invoice_url = data["invoice_url"]

        # Download the invoice PDF
        invoice_response = requests.get(invoice_url)
        if invoice_response.status_code == 200:
            email = EmailMessage(
                subject='Your Order Invoice',
                body='Thank you for your order. Please find your invoice attached.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email],
            )
            email.attach(f'invoice_{order.id}.pdf', invoice_response.content, 'application/pdf')
            email.send()




def about(request):
    return render(request,'user_panel/about.html')

def terms_and_conditions(request):
    return render(request,'user_panel/terms_and_conditions.html') 

def privacy_policy(request):
    return render(request,'user_panel/privacy_policy.html')

from admin_panel.models import Product, Review
from admin_panel.forms import ReviewForm


from django.http import HttpResponseForbidden



@login_required(login_url='email_login')
def write_review(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    # ✅ Ensure user purchased the product
    has_purchased = OrderItem.objects.filter(
        order__user=request.user,
        product=product
    ).exists()

    if not has_purchased:
        return HttpResponseForbidden("You can only review products you've purchased.")

    # ✅ Check if already reviewed this product
    already_reviewed = Review.objects.filter(user=request.user, product=product).exists()
    if already_reviewed:
        messages.error(request, "You've already reviewed this product.")
        return redirect('product_detail', product_id=product.id)

    # ✅ Handle form submission
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.product = product
            review.save()
            messages.success(request, "Thank you for reviewing this product!")
            return redirect('product_detail', product_id=product.id)
    else:
        form = ReviewForm()

    return render(request, 'user_panel/rating.html', {
        'form': form,
        'product': product,
    })

