from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Church, Event, PrayerRequest, Announcement


class ChurchForm(forms.ModelForm):
    class Meta:
        model = Church
        fields = ['name', 'city'] # can add more


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "username",
            "email",
            "password1",
            "password2",
        ]
    def clean_email(self):
        email = self.cleaned_data.get("email")
        
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email already in use")
    
        return email
    

#Form to add Events

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            'name',
            'description',
            'start',
            'end',
            'is_recurring',
            'repeat_type',
            'repeat_until',
            'auto_delete_after_days',
        ]

        widgets = {
            'start': forms.DateTimeInput(attrs={'type': 'datetime-local'}), 
            'end': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'repeat_until': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

        labels = {
            'start': 'Start Date & Time',
            'end': "End Date & Time",
            'repeat_until': 'Repeat Until (optional)',
            'auto_delete_after_days': 'Auto-delete after event ends (days)',
        }

        def clean(self):
            cleaned = super().clean()
            start = cleaned.get('start')
            end = cleaned.get('end')
            recurring = cleaned.get('is_recurring')
            repeat_until = cleaned.get('repeat_until')

            #Validations
            if start and end and end < start:
                raise forms.ValidationError('End date/time must be after start date/time.')
            
            if recurring and not cleaned.get('repeat_type'):
                raise forms.ValidationError('Please select how often this event is repeated.')
            
            if repeat_until and start and repeat_until < start:
                raise forms.ValidationError('Repeat end must be after start.')
            
            return cleaned
        

class PrayerRequestForm(forms.ModelForm):
    class Meta:
        model = PrayerRequest
        fields = ['request', 'is_anonymous']
        widgets = {
            'request': forms.Textarea(attrs={'rows': 4}),
        }

class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ['title', 'message', 'is_pinned']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 4}),
        }