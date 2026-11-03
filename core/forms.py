from django import forms

from .models import PropertyReport


class PropertyReportForm(forms.ModelForm):
    class Meta:
        model = PropertyReport
        fields = ["reason", "description"]
        widgets = {
            "reason": forms.Select(attrs={"class": "form-select"}),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": "Explain the specific problem clearly (at least 20 characters)...",
                }
            ),
        }
        help_texts = {
            "reason": "Choose the reason that best matches the problem.",
            "description": "Please give a clear, specific explanation so the platform team can review it quickly.",
        }

    def clean_description(self):
        description = " ".join(self.cleaned_data.get("description", "").split())
        if len(description) < 20:
            raise forms.ValidationError(
                "Please provide a specific reason with at least 20 characters."
            )
        return description
