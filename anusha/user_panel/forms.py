from datetime import datetime
from django import forms
from .models import *
class OTPForm(forms.Form):
    email = forms.EmailField(max_length=50, widget=forms.EmailInput(attrs={'placeholder': 'Enter email'}))

    otp = forms.CharField(max_length=6, widget=forms.TextInput(attrs={'placeholder': 'Enter OTP'}))


class AddressForm(forms.ModelForm):
    class Meta:
        model = AddressModel
        fields = '__all__'
        exclude=['user','is_blocked']
        widgets = {
            'Name': forms.TextInput(attrs={'placeholder': 'Enter Name', 'class': 'form-control'}),
            'MobileNumber': forms.TextInput(attrs={'placeholder': 'Enter Mobile Number', 'class': 'form-control'}),
            'Alternate_MobileNumber': forms.TextInput(attrs={'placeholder': 'Enter Alternate Mobile Number', 'class': 'form-control'}),
            'Pincode': forms.TextInput(attrs={'placeholder': 'Enter Pincode', 'class': 'form-control'}),
            'City': forms.TextInput(attrs={'placeholder': 'Enter City', 'class': 'form-control'}),
            'State': forms.TextInput(attrs={'placeholder': 'Enter State', 'class': 'form-control'}),
            'location': forms.TextInput(attrs={'placeholder': 'Enter Location/Area/Street', 'class': 'form-control'}),
            'Building': forms.TextInput(attrs={'placeholder': 'Enter Building Name/Flat No./House No.', 'class': 'form-control'}),
            'Landmark': forms.TextInput(attrs={'placeholder': 'Enter Landmark', 'class': 'form-control'}),
        }

    
class Giftform(forms.ModelForm):
    class Meta:
        model = GiftSet
        fields = '__all__'
        # exclude=['product']
        # widgets = {
        #     'gift_set_name': forms.TextInput(attrs={'placeholder': 'Enter Gift Set Name', 'class': 'form-control'}),
        #     'gift_set_price': forms.TextInput(attrs={'placeholder': 'Enter Gift Set Price', 'class': 'form-control'}),
        #     'gift_set_description': forms.Textarea(attrs={'placeholder': 'Enter Gift Set Description', 'class': 'form-control'}),
        #     'gift_set_image': forms.ClearableFileInput(attrs={'placeholder': 'Upload Gift Set Image', 'class': 'form-control'}),
        # }


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = [ 'dob', 'gender', 'profile_image']
        
        widgets = {

            'dob': forms.DateInput(attrs={
                'type': 'date',
                'style': 'border:none; outline:none; font-size:16px; background-color:transparent;',
                'class': 'ms-2'
            }),
            'gender': forms.Select(attrs={  # Changed from RadioSelect to Select
                'style': 'border:none; outline:none; font-size:16px; background-color:transparent;',
                'class': 'ms-2 form-select'
            }),
        }

    def clean_dob(self):
        dob = self.cleaned_data.get('dob')
        if dob and isinstance(dob, str):
            try:
                return datetime.strptime(dob, '%Y-%m-%d').date()
            except ValueError:
                raise forms.ValidationError("Enter a valid date in YYYY-MM-DD format.")
        return dob

class HelpQueryForm(forms.ModelForm):
    class Meta:
        model = HelpQuery
        fields = ['subject', 'message']
        widgets = {
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter subject of your query'
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe your issue in detail'
            }),
        }