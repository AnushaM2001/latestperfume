from django.contrib import admin
from .models import *
# Register your models here.
admin.site.register(Cart)
admin.site.register(AddressModel)

admin.site.register(UserProfile)

admin.site.register(HelpQuery)


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'product__name')
