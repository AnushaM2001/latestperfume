from django.urls import path
from .views import (
    admin_login_view,
    admin_logout_view,
    change_admin_password_view,
    admin_dashboard,
    product_list,
    add_product,
    update_product,
    delete_product,
    view_giftsets,
    view_varaints,
    view_giftsets,
    category_list,
    add_category,
    delete_category,
    edit_category,
    subcategory_list,
    add_subcategory,
    edit_subcategory,
    delete_subcategory,
    flavor_list,
    add_flavor,
    edit_flavor,
    delete_flavor,
    festival_list,
    add_festival,
    edit_festival,
    delete_festival,
    coupon_list,
    add_coupon,
    edit_coupon,
    delete_coupon,
    product_video_list,
    add_product_video,
    edit_product_video,
    delete_product_video,
    Payment_view,
    users_list,
    block_user,
    review_list,
    add_review,
    edit_review,
    delete_review,
    orders_list,
    banner_list,
    add_banner,
    edit_banner,
    delete_banner,
    test_token,
    get_best_courier_view,
    save_subscription,
    get_chart_data,
    socket_test_view,
    admin_help_query_list,
    admin_help_query_reply,mark_notifications_read
    

)

from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path('admin-login/', admin_login_view, name='admin_login'),
    path('admin-logout/', admin_logout_view, name='admin_logout'),
    path('admin-change-password/', change_admin_password_view, name='admin_change_password'),
    path('', admin_dashboard, name='admin_dashboard'),

    # Product Management
    path('products/', product_list, name='product_list'),
    path('products/add/', add_product, name='add_product'),
    path('products/<int:pk>/update/', update_product, name='update_product'),
    path('products/<int:pk>/delete/', delete_product, name='delete_product'),
    path('view-variants/', view_varaints, name='view_variants'),  # Add this line
    path('view-giftsets/', view_giftsets, name='view_giftsets'),  # Add this line

    # Category Management
    path('categories/', category_list, name='category_list'),
    path('categories/add/', add_category, name='add_category'),
    path('categories/<int:pk>/delete/', delete_category, name='delete_category'),
    path('categories/<int:pk>/update/', edit_category, name='update_category'),

    # Subcategory Management
    path('subcategories/', subcategory_list, name='subcategory_list'),
    path('subcategories/add/', add_subcategory, name='add_subcategory'),
    path('subcategories/<int:pk>/update/', edit_subcategory, name='edit_subcategory'),  # Add this
    path('subcategories/<int:pk>/delete/', delete_subcategory, name='delete_subcategory'),  # Add this

    path('flavors/', flavor_list, name='flavor_list'),
    path('flavors/add/', add_flavor, name='add_flavor'),
    path('flavors/<int:pk>/delete/', delete_flavor, name='delete_flavor'),
    path('flavors/<int:pk>/update/', edit_flavor, name='update_flavor'),

    path('festivals/', festival_list, name='festival_list'),
    path('festivals/add/', add_festival, name='add_festival'),
    path('festivals/<int:pk>/delete/', delete_festival, name='delete_festival'),
    path('festivals/<int:pk>/update/', edit_festival, name='update_festival'),

    path('coupons/', coupon_list, name='coupon_list'),
    path('coupons/add/', add_coupon, name='add_coupon'),
    path('coupons/<int:pk>/delete/', delete_coupon, name='delete_coupon'),
    path('coupons/<int:pk>/update/', edit_coupon, name='update_coupon'),

    path('videos/', product_video_list, name='video_list'),
    path('videos/add/', add_product_video, name='add_video'),
    path('videos/<int:pk>/delete/', delete_product_video, name='delete_video'),
    path('videos/<int:pk>/update/', edit_product_video, name='update_video'),

    path('payments/', Payment_view, name='payment_list'),
    path('users/', users_list, name='user_list'),
    path('block-user/<int:user_id>/', block_user, name='block_user'),



    path('reviews/', review_list, name='review_list'),
    path('reviews/add/', add_review, name='add_review'),
    path('reviews/<int:pk>/delete/', delete_review, name='delete_review'),
    path('reviews/<int:pk>/update/', edit_review, name='update_review'),

    path('orders/', orders_list, name='order_list'),

    path('banners/', banner_list, name='banner_list'),
    path('banners/add/', add_banner, name='add_banner'),
    path('banners/<int:pk>/delete/', delete_banner, name='delete_banner'),
    path('banners/<int:pk>/update/', edit_banner, name='update_banner'),
    #shipping===============================================
        path('test-token/', test_token, name='test_token'),
        path('serviceview/<int:address_id>/',get_best_courier_view, name='get_best_courier_view'),
            path('save-subscription/', save_subscription, name='save_subscription'),

    path('chart-data/', get_chart_data, name='chart_data'),
    path('test-socket/', socket_test_view),
    path('notifications/mark-read/<str:category>/', mark_notifications_read, name='mark_notifications_read'),


     path('help-queries/', admin_help_query_list, name='admin_help_query_list'),
    path('help-queries/<int:query_id>/reply/', admin_help_query_reply, name='admin_help_query_reply'),

    


]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
