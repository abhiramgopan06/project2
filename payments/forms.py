import re

from django import forms

from .models import Payment


class MockPaymentForm(forms.Form):
    payment_method = forms.ChoiceField(
        choices=Payment.PaymentMethod.choices,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    card_holder = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Demo User"}),
    )
    card_number = forms.CharField(
        max_length=19,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "4111 1111 1111 1111", "inputmode": "numeric"}),
    )
    expiry = forms.CharField(
        max_length=5,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "12/30"}),
    )
    cvv = forms.CharField(
        max_length=4,
        required=False,
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "123"}),
    )
    simulate_result = forms.ChoiceField(
        choices=(("SUCCESS", "Successful payment"), ("FAILED", "Failed payment")),
        initial="SUCCESS",
        widget=forms.Select(attrs={"class": "form-select"}),
        help_text="This is a mock payment. No real money or card data is processed.",
    )

    def clean(self):
        cleaned = super().clean()
        method = cleaned.get("payment_method")

        if method == Payment.PaymentMethod.MOCK_CARD:
            number = re.sub(r"\D", "", cleaned.get("card_number", ""))
            if len(number) != 16:
                self.add_error("card_number", "Enter a 16-digit demo card number.")
            if not cleaned.get("card_holder"):
                self.add_error("card_holder", "Enter the demo card holder name.")
            expiry = cleaned.get("expiry", "")
            if not re.fullmatch(r"(0[1-9]|1[0-2])/\d{2}", expiry):
                self.add_error("expiry", "Use MM/YY format, for example 12/30.")
            cvv = cleaned.get("cvv", "")
            if not cvv.isdigit() or len(cvv) not in (3, 4):
                self.add_error("cvv", "Enter a 3 or 4 digit demo CVV.")
            cleaned["card_last4"] = number[-4:] if len(number) == 16 else ""
        else:
            cleaned["card_last4"] = ""

        return cleaned
