from django import forms


class OrderForm(forms.Form):
    quantity = forms.IntegerField(min_value=1, max_value=10, initial=1)
