from .models import Category
from admin_panel.models import PremiumFestiveOffer
from django.utils import timezone



def category_subcategory_navbar(request):
    now = timezone.now()

    # Get all categories with subcategories
    categories = Category.objects.prefetch_related('subcategories').order_by('-created_at')

    # Filter for 'Combos' category only if a valid Festival offer exists
    filtered_categories = []
    for category in categories:
        if category.name.startswith('Buy'):
            has_valid_offer = PremiumFestiveOffer.objects.filter(
                premium_festival='Festival',
                is_active=True,
                start_date__lte=now,
                end_date__gte=now,
                category=category
            ).exists()
            if has_valid_offer:
                filtered_categories.append(category)
        else:
            # Add other categories normally
            filtered_categories.append(category)

    return {'navbar_categories': filtered_categories}

# your_app/context_processors.py



def festival_offer_context(request):
    current_time = timezone.now()

    festival_offer = PremiumFestiveOffer.objects.filter(
        premium_festival='Festival',
        start_date__lte=current_time,
        end_date__gt=current_time
    ).order_by('-created_at').first()

    if festival_offer:
        return {
            'festival_offer_percentage': festival_offer.percentage,
            'festival_offer_start': festival_offer.start_date,
            'festival_offer_end': festival_offer.end_date,
            'festival_offer_name': festival_offer.offer_name,
        }
    return {}  # No offer found
