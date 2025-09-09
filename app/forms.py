from django import forms
from .models import Product,Address,Cart,CartItem

class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ["full_name", "phone", "street", "city", "state", "landmark", "pincode"]
        widgets = {
            "full_name": forms.TextInput(attrs={"class": "w-full p-2 border rounded-lg"}),
            "phone": forms.TextInput(attrs={"class": "w-full p-2 border rounded-lg"}),
            "street": forms.TextInput(attrs={"class": "w-full p-2 border rounded-lg"}),
            "city": forms.TextInput(attrs={"class": "w-full p-2 border rounded-lg"}),
            "state": forms.TextInput(attrs={"class": "w-full p-2 border rounded-lg"}),
            "landmark": forms.TextInput(attrs={"class": "w-full p-2 border rounded-lg"}),
            "pincode": forms.TextInput(attrs={"class": "w-full p-2 border rounded-lg"}),
        }

