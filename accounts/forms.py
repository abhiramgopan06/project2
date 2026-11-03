from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import RegexValidator

from .models import User


phone_validator = RegexValidator(
    regex=r"^[0-9]{10}$",
    message="Enter exactly 10 digits for the Indian mobile number.",
)


class RegistrationForm(UserCreationForm):
    phone = forms.CharField(
        required=False,
        validators=[phone_validator],
        widget=forms.TextInput(attrs={"inputmode": "numeric", "maxlength": "10", "pattern": "[0-9]{10}"}),
    )
    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "phone",
            "role",
            "password1",
            "password2",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["role"].choices = [
            (User.Role.TENANT, "Tenant - I want to rent a property"),
            (User.Role.OWNER, "Property Owner - I want to list properties"),
        ]
        self.fields["role"].label = "I am a"
        self.fields["email"].required = True
        self.fields["phone"].required = False

        hints = {
            "username": ("Choose a username", "username"),
            "first_name": ("First name", "given-name"),
            "last_name": ("Last name", "family-name"),
            "email": ("you@gmail.com", "email"),
            "phone": ("Mobile number (optional)", "tel"),
            "password1": ("Create a password", "new-password"),
            "password2": ("Repeat the password", "new-password"),
        }
        for name, field in self.fields.items():
            field.widget.attrs["class"] = "form-select" if name == "role" else "form-control"
            if name in hints:
                field.widget.attrs["placeholder"], field.widget.attrs["autocomplete"] = hints[name]
        self.fields["email"].help_text = "We will email a 6-digit verification code to this address."
        self.fields["password1"].help_text = "At least 8 characters. Avoid common passwords."
        self.fields["password2"].help_text = ""

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email, is_active=True).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email


class ProfileForm(forms.ModelForm):
    phone = forms.CharField(
        required=False,
        validators=[phone_validator],
        widget=forms.TextInput(attrs={"inputmode": "numeric", "maxlength": "10", "pattern": "[0-9]{10}"}),
    )

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "phone", "profile_image"]

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.exclude(pk=self.instance.pk).filter(email__iexact=email).exists():
            raise forms.ValidationError("Another account already uses this email.")
        return email
