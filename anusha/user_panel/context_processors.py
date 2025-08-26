from .models import Category
from admin_panel.models import PremiumFestiveOffer
from django.utils import timezone



def category_subcategory_navbar(request):
    now = timezone.now()

    # ---------------------------
    # 1. Navbar Categories Logic
    # ---------------------------
    categories = Category.objects.prefetch_related('subcategories').order_by('-created_at')

    navbar_categories = []
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
                navbar_categories.append(category)
        else:
            navbar_categories.append(category)

    # ---------------------------
    # 2. Category Section Logic
    # ---------------------------
    section_categories = []

    for category in categories:
        if category.name.startswith("Buy"):
            has_offer = PremiumFestiveOffer.objects.filter(
                premium_festival='Festival',
                is_active=True,
                start_date__lte=now,
                end_date__gte=now,
                category=category
        ).exists()
            if has_offer:
                section_categories.append(category)
        else:
            section_categories.append(category)

        if len(section_categories) == 4:
            break

# fallback: if still empty, just take latest 4
    if not section_categories:
        section_categories = categories[:4]


    return {
        "navbar_categories": navbar_categories,
        "section_categories": section_categories,
    }

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
            'festival_offer_category': ', '.join(festival_offer.category.values_list('name', flat=True)),
            'festival_offer_category_ids': list(festival_offer.category.values_list('id', flat=True)),
            'festival_offer_subcategory': ', '.join(festival_offer.subcategory.values_list('name', flat=True)),
            'festival_offer_subcategory_ids': list(festival_offer.subcategory.values_list('id', flat=True)),
        }
    return {}  # No offer found
