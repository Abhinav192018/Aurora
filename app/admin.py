from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Sum, Count
from django.contrib.admin import SimpleListFilter
from app.models import Type, Category, Product, Color, Gift, Order, OrderItem, Address, Cart, CartItem, Wishlist

# Admin Site Configuration
admin.site.site_header = "AURORA CADENCE"
admin.site.site_title = "AURORA CADENCE Admin Portal"
admin.site.index_title = "Welcome to AURORA CADENCE Admin"

# Custom Filters
class StockLevelFilter(admin.SimpleListFilter):
    title = 'Stock Level'
    parameter_name = 'stock_level'

    def lookups(self, request, model_admin):
        return (
            ('out_of_stock', 'Out of Stock (0)'),
            ('low_stock', 'Low Stock (1-5)'),
            ('medium_stock', 'Medium Stock (6-20)'),
            ('high_stock', 'High Stock (21-50)'),
            ('excellent_stock', 'Excellent Stock (50+)'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'out_of_stock':
            return queryset.filter(stock=0)
        elif self.value() == 'low_stock':
            return queryset.filter(stock__range=(1, 5))
        elif self.value() == 'medium_stock':
            return queryset.filter(stock__range=(6, 20))
        elif self.value() == 'high_stock':
            return queryset.filter(stock__range=(21, 50))
        elif self.value() == 'excellent_stock':
            return queryset.filter(stock__gt=50)
        return queryset

class PaymentStatusFilter(admin.SimpleListFilter):
    title = 'Payment Status'
    parameter_name = 'payment_status'

    def lookups(self, request, model_admin):
        return (
            ('Paid', 'Paid'),
            ('Pending', 'Pending'),
            ('Failed', 'Failed'),
            ('Cancelled', 'Cancelled'),
        )

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(payment_status=self.value())
        return queryset

class OrderStatusFilter(admin.SimpleListFilter):
    title = 'Order Status'
    parameter_name = 'order_status'

    def lookups(self, request, model_admin):
        return (
            ('Pending', 'Pending'),
            ('Confirmed', 'Confirmed'),
            ('Shipped', 'Shipped'),
            ('Delivered', 'Delivered'),
            ('Cancelled', 'Cancelled'),
        )

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(status=self.value())
        return queryset

# Product Admin
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    def image_tag(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:80px; width:80px; object-fit:cover; border-radius:8px;"/>', obj.image.url)
        return format_html('<span style="color: #999;">No Image</span>')
    image_tag.short_description = 'Product Image'

    def stock_status(self, obj):
        if obj.stock == 0:
            return format_html('<span style="color: #dc3545; font-weight: bold;">Out of Stock</span>')
        elif obj.stock <= 5:
            return format_html('<span style="color: #ffc107; font-weight: bold;">Low Stock ({})</span>', obj.stock)
        elif obj.stock <= 20:
            return format_html('<span style="color: #fd7e14; font-weight: bold;">Medium Stock ({})</span>', obj.stock)
        else:
            return format_html('<span style="color: #28a745; font-weight: bold;">In Stock ({})</span>', obj.stock)
    stock_status.short_description = 'Stock Status'

    def price_display(self, obj):
        if obj.price > obj.discount_price:
            return format_html(
                '<span style="text-decoration: line-through; color: #999;">₹{}</span><br>'
                '<span style="color: #dc3545; font-weight: bold;">₹{}</span>',
                obj.price, obj.discount_price
            )
        return format_html('<span style="font-weight: bold;">₹{}</span>', obj.price)
    price_display.short_description = 'Price'

    list_display = (
        'image_tag', 'name', 'type_obj', 'category_obj', 'price_display', 
        'stock_status', 'is_available', 'created_at'
    )
    list_filter = (
        'category_obj', 'type_obj', 'gift_obj', 'wear', 'is_available', 
        'created_at', StockLevelFilter
    )
    search_fields = ('name', 'description', 'gift_obj__name', 'category_obj__name', 'type_obj__name')
    readonly_fields = ('created_at', 'updated_at')
    list_per_page = 20
    ordering = ('-created_at',)

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'type_obj', 'category_obj', 'Color_obj', 'gift_obj', 'wear', 'description')
        }),
        ('Pricing & Stock', {
            'fields': ('price', 'discount_price', 'stock', 'is_available')
        }),
        ('Images', {
            'fields': ('image', 'image2', 'image3', 'image4', 'image5'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

# Order Item Inline
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product_image', 'product_name', 'quantity', 'price_at_time', 'discount_price_at_time', 'total_amount')
    fields = ('product_image', 'product_name', 'quantity', 'price_at_time', 'discount_price_at_time', 'total_amount')

    def product_image(self, obj):
        if obj.product.image:
            return format_html('<img src="{}" style="height:50px; width:50px; object-fit:cover; border-radius:4px;"/>', obj.product.image.url)
        return "No Image"
    product_image.short_description = 'Image'

    def product_name(self, obj):
        return obj.product.name
    product_name.short_description = 'Product'

    def total_amount(self, obj):
        return f"₹{obj.discounted_total()}"
    total_amount.short_description = 'Total'

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('product')

# Order Admin with comprehensive details
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    def order_id_display(self, obj):
        return format_html('<strong style="color: #007bff;">#{}</strong>', obj.id)
    order_id_display.short_description = 'Order ID'

    def customer_info(self, obj):
        return format_html(
            '<div style="line-height: 1.4;">'
            '<strong>{}</strong><br>'
            '<small style="color: #666;">{}</small><br>'
            '<small style="color: #666;">ID: {}</small>'
            '</div>',
            obj.user.get_full_name() or obj.user.username,
            obj.user.email,
            obj.user.id
        )
    customer_info.short_description = 'Customer'

    def address_display(self, obj):
        if obj.shipping_address:
            return format_html(
                '<div style="line-height: 1.4; max-width: 250px;">'
                '<strong>{}</strong><br>'
                '<small>{}</small><br>'
                '<small>Landmark: {}</small><br>'
                '<small>{}, {}</small><br>'
                '<small>Phone: {}</small>'
                '</div>',
                obj.shipping_address.full_name,
                obj.shipping_address.street,
                obj.shipping_address.landmark or "N/A",  # safe fallback
                obj.shipping_address.city,
                obj.shipping_address.state,
                obj.shipping_address.phone
            )
        return format_html('<span style="color: #dc3545;">No Address</span>')
    address_display.short_description = 'Shipping Address'

    def payment_status_display(self, obj):
        status_colors = {
            'Paid': '#28a745',
            'Pending': '#ffc107',
            'Failed': '#dc3545',
            'Cancelled': '#6c757d'
        }
        color = status_colors.get(obj.payment_status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold;">{}</span>',
            color, obj.payment_status
        )
    payment_status_display.short_description = 'Payment'

    def order_status_display(self, obj):
        status_colors = {
            'Confirmed': '#28a745',
            'Pending': '#ffc107',
            'Shipped': '#17a2b8',
            'Delivered': '#28a745',
            'Cancelled': '#dc3545'
        }
        color = status_colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold;">{}</span>',
            color, obj.status
        )
    order_status_display.short_description = 'Status'

    def total_display(self, obj):
        return format_html('<strong style="color: #28a745; font-size: 16px;">₹{}</strong>', obj.total_price)
    total_display.short_description = 'Total'

    def items_count(self, obj):
        count = obj.order_items.count()
        return format_html('<span style=" color: black; padding: 2px 6px; border-radius: 12px; font-size: 18px;">{} items</span>', count)
    items_count.short_description = 'Items'

    def payment_info(self, obj):
        info = []
        if obj.payment_id:
            info.append(f"Payment ID: {obj.payment_id}")
        if obj.razorpay_order_id:
            info.append(f"Razorpay: {obj.razorpay_order_id}")
        if info:
            return format_html('<br>'.join(info))
        return "No payment info"
    payment_info.short_description = 'Payment Details'

    list_display = (
        'order_id_display', 'customer_info', 'address_display', 'items_count',
        'total_display', 'payment_status_display', 'order_status_display', 
        'ordered_at'
    )
    list_filter = (
        PaymentStatusFilter, OrderStatusFilter, 'ordered_at', 'updated_at'
    )
    search_fields = (
        'user__username', 'user__email', 'user__first_name', 'user__last_name',
        'id', 'razorpay_order_id', 'payment_id', 'shipping_address__full_name',
        'shipping_address__phone'
    )
    readonly_fields = (
        'order_id_display', 'customer_info', 'address_display', 'payment_info',
        'total_display', 'ordered_at', 'updated_at'
    )
    inlines = [OrderItemInline]
    list_per_page = 25
    ordering = ('-ordered_at',)
    actions = ['mark_as_confirmed', 'mark_as_shipped', 'mark_as_delivered', 'mark_as_cancelled']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'user', 'shipping_address'
        ).prefetch_related('order_items__product')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    # Admin Actions
    def mark_as_confirmed(self, request, queryset):
        updated = queryset.update(status='Confirmed')
        self.message_user(request, f'{updated} order(s) marked as confirmed.')
    mark_as_confirmed.short_description = "Mark selected orders as confirmed"

    def mark_as_shipped(self, request, queryset):
        updated = queryset.update(status='Shipped')
        self.message_user(request, f'{updated} order(s) marked as shipped.')
    mark_as_shipped.short_description = "Mark selected orders as shipped"

    def mark_as_delivered(self, request, queryset):
        updated = queryset.update(status='Delivered')
        self.message_user(request, f'{updated} order(s) marked as delivered.')
    mark_as_delivered.short_description = "Mark selected orders as delivered"

    def mark_as_cancelled(self, request, queryset):
        updated = queryset.update(status='Cancelled', payment_status='Cancelled')
        self.message_user(request, f'{updated} order(s) marked as cancelled.')
    mark_as_cancelled.short_description = "Mark selected orders as cancelled"

# Address Admin
@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    def customer_info(self, obj):
        return format_html(
            '<div style="line-height: 1.4;">'
            '<strong>{}</strong><br>'
            '<small style="color: #666;">{}</small>'
            '</div>',
            obj.user.get_full_name() or obj.user.username,
            obj.user.email
        )
    customer_info.short_description = 'Customer'

    def full_address(self, obj):
        return format_html(
            '<div style="line-height: 1.4; max-width: 300px;">'
            '<strong>{}</strong><br>'
            '<small>{}</small><br>'
            '<small>Landmark: {}</small><br>'
            '<small>{}, {} - {}</small><br>'
            '<small>Phone: {}</small>'
            '</div>',
            obj.full_name,
            obj.street,
            obj.landmark or "N/A",  # safe fallback
            obj.city,
            obj.state,
            obj.pincode,
            obj.phone
        )
    full_address.short_description = 'Address Details'

    list_display = ('customer_info', 'full_address', 'created_at')
    list_filter = ('state', 'city', 'created_at')
    search_fields = ('full_name', 'phone', 'city', 'state', 'pincode', 'user__username', 'user__email')
    readonly_fields = ('created_at',)
    list_per_page = 20
    ordering = ('-created_at',)

# Other Model Admins
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'products_count')
    search_fields = ('name',)
    ordering = ('name',)

    def products_count(self, obj):
        return obj.category_obj.count()
    products_count.short_description = 'Products'

@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    ordering = ('name',)

@admin.register(Type)
class TypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'products_count')
    search_fields = ('name',)
    ordering = ('name',)

    def products_count(self, obj):
        return obj.type_obj.count()
    products_count.short_description = 'Products'

@admin.register(Gift)
class GiftAdmin(admin.ModelAdmin):
    list_display = ('name', 'products_count')
    search_fields = ('name',)
    ordering = ('name',)

    def products_count(self, obj):
        return obj.gift_to_obj.count()
    products_count.short_description = 'Products'

# Cart and CartItem Admin (for debugging purposes)
@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    def customer_info(self, obj):
        return format_html(
            '<div style="line-height: 1.4;">'
            '<strong>{}</strong><br>'
            '<small style="color: #666;">{}</small>'
            '</div>',
            obj.user.get_full_name() or obj.user.username,
            obj.user.email
        )
    customer_info.short_description = 'Customer'

    def items_count(self, obj):
        count = obj.items.count()
        return format_html('<span style="background-color: #007bff; color: white; padding: 2px 6px; border-radius: 12px; font-size: 11px;">{} items</span>', count)
    items_count.short_description = 'Items'

    list_display = ('customer_info', 'items_count')
    search_fields = ('user__username', 'user__email')
    ordering = ('-id',)

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ('product_image', 'product_name', 'quantity', 'total_price')
    fields = ('product_image', 'product_name', 'quantity', 'total_price')

    def product_image(self, obj):
        if obj.product.image:
            return format_html('<img src="{}" style="height:40px; width:40px; object-fit:cover; border-radius:4px;"/>', obj.product.image.url)
        return "No Image"
    product_image.short_description = 'Image'

    def product_name(self, obj):
        return obj.product.name
    product_name.short_description = 'Product'

    def total_price(self, obj):
        return f"₹{obj.discounted_total()}"
    total_price.short_description = 'Total'

    def has_add_permission(self, request, obj=None):
        return False

# Wishlist Admin
@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    def customer_info(self, obj):
        return format_html(
            '<div style="line-height: 1.4;">'
            '<strong>{}</strong><br>'
            '<small style="color: #666;">{}</small>'
            '</div>',
            obj.user.get_full_name() or obj.user.username,
            obj.user.email
        )
    customer_info.short_description = 'Customer'

    def product_info(self, obj):
        return format_html(
            '<div style="line-height: 1.4;">'
            '<strong>{}</strong><br>'
            '<small style="color: #666;">₹{}</small>'
            '</div>',
            obj.product.name,
            obj.product.discount_price
        )
    product_info.short_description = 'Product'

    list_display = ('customer_info', 'product_info', 'added_at')
    list_filter = ('added_at',)
    search_fields = ('user__username', 'user__email', 'product__name')
    readonly_fields = ('added_at',)
    list_per_page = 20
    ordering = ('-added_at',)
