from django import forms
from .models import Trip
from datetime import date

COUNTRY_CHOICES = [
    ("", "🌍 Select Country"),
    ("India", "India"),
    ("Nepal", "Nepal"),
    ("Bhutan", "Bhutan"),
    ("Thailand", "Thailand"),
    ("United Arab Emirates", "United Arab Emirates"),
    ("United States", "United States"),
    ("United Kingdom", "United Kingdom"),
    ("Canada", "Canada"),
    ("Australia", "Australia"),
    ("Germany", "Germany"),
    ("France", "France"),
    ("Italy", "Italy"),
    ("Japan", "Japan"),
    ("South Korea", "South Korea"),
    ("Singapore", "Singapore"),
    ("Malaysia", "Malaysia"),
    ("Indonesia", "Indonesia"),
    ("Sri Lanka", "Sri Lanka"),
    ("Maldives", "Maldives"),
    ("Saudi Arabia", "Saudi Arabia"),
    ("Qatar", "Qatar"),
    ("Turkey", "Turkey"),
    ("Spain", "Spain"),
    ("Netherlands", "Netherlands"),
    ("Switzerland", "Switzerland"),
    ("Sweden", "Sweden"),
    ("Norway", "Norway"),
    ("Brazil", "Brazil"),
    ("Argentina", "Argentina"),
    ("South Africa", "South Africa"),
    ("Egypt", "Egypt"),
]

class TripForm(forms.ModelForm):
    country = forms.ChoiceField(
        choices=COUNTRY_CHOICES,
        widget=forms.Select(attrs={"class": "form-control"})
    )

    class Meta:
        model = Trip
        # ✅ ADD THIS LINE
        fields = ["country", "start_location", "start_date", "end_date", "budget", "notes"]

        widgets = {
            "start_location": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter your start location"
            }),

            "start_date": forms.DateInput(attrs={
                "type": "date",
                "class": "form-control"
            }),

            "end_date": forms.DateInput(attrs={
                "type": "date",
                "class": "form-control"
            }),

            "budget": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Enter budget"
            }),

            "notes": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Extra notes"
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")

        today = date.today()

        if start_date and start_date < today:
            self.add_error("start_date", "Start date cannot be in the past.")

        if end_date and end_date < today:
            self.add_error("end_date", "End date cannot be in the past.")

        if start_date and end_date and end_date < start_date:
            self.add_error("end_date", "End date cannot be earlier than start date.")

        return cleaned_data