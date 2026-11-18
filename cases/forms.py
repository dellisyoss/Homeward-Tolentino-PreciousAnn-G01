from django import forms
from django.utils import timezone

from accounts.forms import style_fields
from .models import LostPetCase, Zone


class CaseForm(forms.ModelForm):
    class Meta:
        model = LostPetCase
        fields = (
            "pet_name", "species", "breed", "color", "description",
            "lost_at", "last_known_location", "zone",
        )
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "lost_at": forms.DateTimeInput(
                format="%Y-%m-%dT%H:%M:%S",
                attrs={"type": "datetime-local", "step": "1"},
            ),
        }
        help_texts = {"lost_at": "Use Philippine time (UTC+8)."}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self.fields)

    def clean_lost_at(self):
        lost_at = self.cleaned_data["lost_at"]
        now = timezone.now()
        if lost_at > now:
            raise forms.ValidationError("The time lost cannot be in the future.")
        self.instance.created_at = now
        return lost_at


class ZoneForm(forms.ModelForm):
    class Meta:
        model = Zone
        fields = ("zone_name",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self.fields)
