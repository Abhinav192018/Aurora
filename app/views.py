from django.shortcuts import render,get_object_or_404,redirect
from app.models import Product,Cart,CartItem,Address,Category,Type,Color,Wishlist,Order,OrderItem
from rapidfuzz import fuzz

# Create your views here.
from django.contrib.auth.decorators import login_required

def login_view(request):
    next_url = request.GET.get('next', '/')
    return render(request, 'main_page/login.html', {'next': next_url})

def base(request):
    category = Category.objects.all()
    
    context = {
        'category': category,
    }
    return render(request, 'base.html', context)

def index(request):
    category=Category.objects.all()
    products= Product.objects.all().order_by('-id')[:14]
    

    context={
        'category': category,
        'products': products
    }
    return render(request, 'main_page/index.html',context)




from django.db.models import Q
@login_required
def Products(request):

    query=request.GET.get('q')
    type_name=request.GET.get('type')
    wear_type=request.GET.get('wear')
    gift_name=request.GET.get('gift')
    show_latest = request.GET.get('new')
    category_filter = request.GET.get('category')
    price_filter = request.GET.get('price')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    products=Product.objects.order_by('-id')

    wishlist_ids = []

    if request.user.is_authenticated:
        wishlist_ids = Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True)


    if price_filter:
        if price_filter.isdigit():
            products = products.filter(discount_price__lte=int(price_filter))
        elif price_filter == "premium":
            products = products.filter(discount_price__gt=899)
        
    if category_filter:
        products = products.filter(category_obj__name__iexact=category_filter)

    if show_latest:
        products = products[:12]

    if gift_name:
        products=products.filter(gift_obj__name__iexact=gift_name)

    if type_name:
        products=products.filter(type_obj__name__iexact=type_name)

    if wear_type:
        products=products.filter(wear__iexact=wear_type)

    if query:
        product_list = []
        for product in products:
            text = f"{product.name} {product.category_obj.name} {product.type_obj.name}"
            ratio = fuzz.partial_ratio(query.lower(), text.lower())
            if ratio > 70:  # adjust threshold
                product_list.append(product)
        products = product_list


    if min_price:
        products=products.filter(discount_price__gte=min_price)

    if max_price:
        products=products.filter(discount_price__lte=max_price)


    context = {
        'products':products,
        'selected_type':type_name,
        'selected_wear':wear_type,
        'selected_gift':gift_name,
        'search_query':query,
        'min_price': min_price,
        'max_price': max_price,
        'wishlist_ids': wishlist_ids,
    }
    return render(request, 'main_page/products.html', context)



def Product_details(request, id):
    product=get_object_or_404(Product, id=id)

    related_products = Product.objects.filter(
        type_obj=product.type_obj
    ).exclude(id=product.id)

    context = {
        'product': product,
        'related_products': related_products
    }
    return render(request, 'main_page/product_details.html', context)






from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages


@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)

    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        cart_item.quantity += 1
        cart_item.save()
        messages.success(request, f"Updated quantity of '{product.name}' in your cart.")
    else:
        messages.success(request, f"'{product.name}' has been added to your cart.")

    return HttpResponseRedirect(reverse('products'))


@login_required
def update_cart_quantity(request, item_id, action):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    product = cart_item.product

    if action == 'increase':
        # Check if requested quantity is available
        if cart_item.quantity + 1 > product.stock:
            messages.warning(request, f"Sorry, only {product.stock} units available.")
            return HttpResponseRedirect(reverse('cart'))
            
        cart_item.quantity += 1
        messages.info(request, f"Increased quantity of '{cart_item.product.name}'.")
    elif action == 'decrease' and cart_item.quantity > 1:
        cart_item.quantity -= 1
        messages.info(request, f"Decreased quantity of '{cart_item.product.name}'.")
    
    cart_item.save()
    return HttpResponseRedirect(reverse('cart'))


@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.delete()
    messages.warning(request,f"Removed '{cart_item.product.name}' from your cart.")
    return HttpResponseRedirect(reverse('cart'))

@login_required
def cart(request):
    cart = Cart.objects.get(user=request.user)
    items = cart.items.select_related('product').all()

    original_total = sum(item.total_price() for item in items)
    discounted_total = sum(item.discounted_total() for item in items)
    discount_amount = original_total - discounted_total

    context = {
        'items': items,
        'original_total': original_total,
        'discounted_total': discounted_total,
        'discount_amount': discount_amount
    }
    return render(request, 'main_page/cart.html', context)


@login_required
def toggle_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    wishlist_item = Wishlist.objects.filter(user=request.user, product=product)

    if wishlist_item.exists():
        wishlist_item.delete()  # Remove if already in wishlist
    else:
        Wishlist.objects.create(user=request.user, product=product)  # Add if not

    return redirect(request.META.get('HTTP_REFERER', 'products'))  # Go back to previous page

@login_required
def Delete_wishlist(request,product_id):
    product=get_object_or_404(Product,id=product_id)
    Wishlist.objects.filter(user=request.user,product=product).delete()
    return redirect('wishlist')

@login_required
def wishlist_view(request):
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('product')
    return render(request, 'main_page/wishlist.html', {'wishlist_items': wishlist_items})


@login_required
def MyAccount(request):
    user = request.user
    profile_pic = None
    google_id = None
    locale = None
    google_profile = None
    name = user.get_full_name() or user.username
    if user.social_auth.exists():
        social = user.social_auth.get(provider='google-oauth2')
        extra = social.extra_data
        profile_pic = extra.get('picture')
        google_id = social.uid
        locale = extra.get('locale')
        google_profile = extra.get('profile')
        name = extra.get('name', name)
    context = {
        'email': user.email,
        'profile_pic': profile_pic,
        'google_id': google_id,
        'locale': locale,
        'google_profile': google_profile,
        'name': name,
    }
    return render(request, 'main_page/my_account.html', context)


from .forms import AddressForm


import razorpay
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

# Initialize Razorpay Client
razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

@login_required
def checkout(request):
    try:
        cart = Cart.objects.get(user=request.user)
        items = cart.items.all()
        addresses = Address.objects.filter(user=request.user)

        if not items.exists():
            messages.error(request, "Your cart is empty.")
            return redirect('cart')

        total_price = sum(item.discounted_total() for item in items)
        amount_paise = int(total_price * 100)  # Razorpay works in paise

        # Check if Razorpay keys are configured
        if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
            messages.error(request, "Payment gateway is not configured. Please contact support.")
            return redirect('cart')

        # Create Razorpay order
        razorpay_order = razorpay_client.order.create(dict(
            amount=amount_paise,
            currency="INR",
            payment_capture="1"
        ))

        context = {
            "items": items,
            "addresses": addresses,
            "total_price": total_price,
            "razorpay_key": settings.RAZORPAY_KEY_ID,
            "razorpay_order_id": razorpay_order["id"],
            "amount_paise": amount_paise,
        }
        return render(request, "main_page/checkout.html", context)
        
    except Exception as e:
        messages.error(request, f"Error creating payment order: {str(e)}")
        return redirect('cart')


@login_required
def Add_address(request):
    if request.method == "POST":
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()
            messages.success(request, "Address added successfully.")
            return redirect('checkout')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = AddressForm()
    return render(request, 'main_page/add_address.html', {'form': form})


def Edit_address(request,id):
    address=get_object_or_404(Address,id=id)
    if request.method=="POST":
        form=AddressForm(request.POST,instance=address)
        if form.is_valid():
            form.save()
            messages.success(request,"Address updated successfully.")
            return redirect('checkout')
    else:
        form=AddressForm(instance=address)
    return render(request,'main_page/add_address.html',{'form':form})


def Delete_address(request,id):
    address=get_object_or_404(Address,id=id)
    address.delete()
    return redirect("checkout")


@csrf_exempt
def payment_success(request):
    if request.method == "POST":
        try:
            # Get payment verification data
            razorpay_payment_id = request.POST.get('razorpay_payment_id')
            razorpay_order_id = request.POST.get('razorpay_order_id')
            razorpay_signature = request.POST.get('razorpay_signature')
            address_id = request.POST.get('address')

            # Get cart and address
            cart = Cart.objects.get(user=request.user)
            address = Address.objects.get(id=address_id)
            
            # Calculate total
            total_price = sum(item.discounted_total() for item in cart.items.all())

            # Create order
            order = Order.objects.create(
                user=request.user,
                shipping_address=address,
                total_price=total_price,
                payment_status='Paid',
                status='Confirmed',
                payment_id=razorpay_payment_id,
                razorpay_order_id=razorpay_order_id
            )

            # Create order items and update stock
            for cart_item in cart.items.all():
                # Create order item
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    quantity=cart_item.quantity,
                    price_at_time=cart_item.product.price,
                    discount_price_at_time=cart_item.product.discount_price
                )
                
                # Update product stock
                product = cart_item.product
                product.stock -= cart_item.quantity  # Decrease stock by purchased quantity
                if product.stock <= 0:
                    product.is_available = False  # Mark as unavailable if out of stock
                product.save()

            # Clear cart
            cart.items.all().delete()

            messages.success(request, 'Order placed successfully!')
            return redirect('my_orders')

        except Exception as e:
            messages.error(request, f'Error processing order: {str(e)}')
            return redirect('checkout')

    return redirect('checkout')



@csrf_exempt
def payment_failed(request):
    if request.method == "POST":
        error_code = request.POST.get("error_code")
        error_description = request.POST.get("error_description")
        razorpay_order_id = request.POST.get("razorpay_order_id")
        address_id = request.POST.get("address")
        
        try:
            cart = Cart.objects.get(user=request.user)
            items = cart.items.all()
            
            if items.exists():
                total_price = sum(item.discounted_total() for item in items)
                address = None
                if address_id:
                    address = get_object_or_404(Address, id=address_id, user=request.user)
                
                # Create failed order record
                order = Order.objects.create(
                    user=request.user,
                    total_price=total_price,
                    status="Cancelled",
                    payment_status="Failed",
                    razorpay_order_id=razorpay_order_id,
                    shipping_address=address
                )
                
                # Create order items from cart items for failed order
                for item in items:
                    OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        quantity=item.quantity,
                        price_at_time=item.product.price,
                        discount_price_at_time=item.product.discount_price
                    )
                
                messages.error(request, f"Payment failed: {error_description}")
            else:
                messages.error(request, "Payment failed: No items found in cart.")
        except Exception as e:
            messages.error(request, f"Error processing failed payment: {str(e)}")
    else:
        messages.error(request, "Payment was cancelled or failed.")
    
    return redirect('checkout')


from datetime import timedelta
@login_required
def my_orders(request):
    # Get all orders for the current user, ordered by most recent first
    orders = Order.objects.filter(user=request.user).order_by('-ordered_at')
    
    for order in orders:
        order.estimated_delivery = order.ordered_at+timedelta(days=5)

    context = {
        'orders': orders,
    }
    return render(request, 'main_page/my_orders.html', context)