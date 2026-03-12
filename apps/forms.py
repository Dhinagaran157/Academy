from django import forms
from .models import admission
from .models import Staff
import re

class EnquiryForm(forms.ModelForm):
    class Meta:
        model = admission
        fields = ['full_name', 'phone', 'whatsapp', 'email', 'mode', 
                 'graduation_year', 'course', 'message']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control py-3 px-4 fs-6 fw-500', 'placeholder': 'Your Full Name *', 'required': True}),
            'phone': forms.TextInput(attrs={'type': 'tel', 'class': 'form-control py-3 px-4 fs-6 fw-500', 'placeholder': 'Phone Number *', 'required': True}),
            'whatsapp': forms.TextInput(attrs={'type': 'tel', 'class': 'form-control py-3 px-4 fs-6 fw-500', 'placeholder': 'WhatsApp Number *', 'required': True}),
            'email': forms.EmailInput(attrs={'class': 'form-control py-3 px-4 fs-6 fw-500', 'placeholder': 'Email Address *', 'required': True}),
            'mode': forms.Select(attrs={'class': 'form-select py-3 px-4 fs-6 fw-500', 'style': 'border-radius: 16px;', 'required': True}),
            'graduation_year': forms.Select(attrs={'class': 'form-select py-3 px-4 fs-6 fw-500', 'style': 'border-radius: 16px;', 'required': True}),
            'course': forms.Select(attrs={'class': 'form-select py-3 px-4 fs-6 fw-500', 'style': 'border-radius: 16px;', 'required': True}),
            'message': forms.Textarea(attrs={'class': 'form-control py-3 px-4 fs-6', 'rows': 3, 'placeholder': 'Tell us about your career goals... (optional)', 'style': 'border-radius: 16px;'}),
        }



# forms.py



class StaffForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = Staff
        fields = ['first_name', 'last_name', 'email', 'phone', 'department']

    # 🔹 Validate Email
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Staff.objects.filter(email=email).exists():
            raise forms.ValidationError("Email already exists!")
        return email

    # 🔹 Validate Phone
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            if not re.match(r'^[6-9]\d{9}$', phone):
                raise forms.ValidationError("Enter valid 10-digit phone number.")
        return phone

    # 🔹 Validate Password
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password2 = cleaned_data.get("password2")

        if password and len(password) < 8:
            raise forms.ValidationError("Password must be at least 8 characters.")

        if password != password2:
            raise forms.ValidationError("Passwords do not match!")

        return cleaned_data