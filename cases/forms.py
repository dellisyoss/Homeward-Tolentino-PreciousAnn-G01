from io import BytesIO

from django import forms
from django.utils import timezone
from PIL import Image, ImageOps

from accounts.forms import style_fields
from .models import STATUS_TRANSITIONS, LostPetCase, Status, Zone


class CaseForm(forms.ModelForm):
    photo = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={"accept": "image/jpeg,image/png,image/webp"}),
        help_text="JPEG, PNG, or WebP, up to 2 MB and 12 megapixels.",
    )
    remove_photo = forms.BooleanField(required=False)

    class Meta:
        model = LostPetCase
        fields = (
            "pet_name", "species", "breed", "color", "description", "lost_at",
            "last_known_location", "zone", "status", "photo", "remove_photo",
        )
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "lost_at": forms.DateTimeInput(
                format="%Y-%m-%dT%H:%M:%S",
                attrs={"type": "datetime-local", "step": "1"},
            ),
        }
        help_texts = {"lost_at": "Use Philippine time (UTC+8)."}
        error_messages = {
            "species": {"invalid_choice": "Choose Dog, Cat, or Other."},
            "lost_at": {"invalid": "Enter a valid date and time."},
            "zone": {"required": "Choose a zone.", "invalid_choice": "Choose an available zone."},
            "status": {"invalid_choice": "This case cannot change to that status."},
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            current = Status(self.instance.status)
            allowed = (current, *STATUS_TRANSITIONS[current])
            self.fields["status"].choices = [(value, value.label) for value in allowed]
        else:
            self.fields.pop("status")
        if not self.instance.photo_data:
            self.fields.pop("remove_photo")
        self.has_zones = self.fields["zone"].queryset.exists()
        style_fields(self.fields)

    def clean_lost_at(self):
        lost_at = self.cleaned_data["lost_at"]
        now = timezone.now()
        if lost_at > now:
            raise forms.ValidationError("The time lost cannot be in the future.")
        if self.instance.pk and lost_at > self.instance.created_at:
            raise forms.ValidationError("The time lost cannot be after the case was created.")
        if not self.instance.pk:
            self.instance.created_at = now
        return lost_at

    def clean_photo(self):
        uploaded = self.cleaned_data["photo"]
        if not uploaded:
            return None
        if uploaded.size > 2 * 1024 * 1024:
            raise forms.ValidationError("Choose a photo no larger than 2 MB.")
        try:
            with Image.open(uploaded, formats=("JPEG", "PNG", "WEBP")) as image:
                if image.width * image.height > 12_000_000:
                    raise forms.ValidationError("Choose a photo no larger than 12 megapixels.")
                image = ImageOps.exif_transpose(image).convert("RGB")
                image.thumbnail((1200, 1200))
                output = BytesIO()
                image.save(output, format="JPEG", quality=85)
                return output.getvalue()
        except Image.DecompressionBombError as exc:
            raise forms.ValidationError("Choose a photo no larger than 12 megapixels.") from exc
        except (OSError, SyntaxError, ValueError) as exc:
            raise forms.ValidationError("Choose a valid JPEG, PNG, or WebP photo.") from exc

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("photo") and cleaned.get("remove_photo"):
            self.add_error("remove_photo", "Choose either to replace or remove the current photo.")
        return cleaned

    def save(self, commit=True):
        case = super().save(commit=False)
        if self.cleaned_data["photo"]:
            case.photo_data = self.cleaned_data["photo"]
        elif self.cleaned_data.get("remove_photo"):
            case.photo_data = None
        if commit:
            case.save()
        return case


class ZoneForm(forms.ModelForm):
    class Meta:
        model = Zone
        fields = ("zone_name",)
        error_messages = {
            "zone_name": {"required": "Enter a zone name.", "unique": "That zone name already exists."},
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self.fields)
