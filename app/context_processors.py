from .models import CartItem

def cart_items_processor(request):
    if request.user.is_authenticated and hasattr(request.user, 'cart'):
        items = request.user.cart.items.select_related('product')
        total_quantity = items.count()
        return {
            'cart_items': items,
            'cart_total_quantity': total_quantity,
        }
    return {
        'cart_items': [],
        'cart_total_quantity': 0,
    }






