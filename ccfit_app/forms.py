from django import forms
from ccfit_app.models import UserProfileInfo, Workout
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import User


# The following two models are responsible for the
# date field on the booking sessions page
class DateInput(forms.DateInput):
    input_type = 'date'

class ExampleForm(forms.Form):
    my_date_field = forms.DateField(widget=DateInput)


# Form
# class WorkoutForm(forms.ModelForm):
#     class Meta:
#         model = Workout
#         fields = [
#                 'date',
#                 'email_user',
#                 'session_number',
#         ]

# The following 5 forms are used all for users but in
# different files
class SignUpForm(UserCreationForm):
    username = forms.CharField(max_length=50)
    first_name = forms.CharField(max_length=100)
    last_name = forms.CharField(max_length=100)

    class Meta:
        model = get_user_model()
        fields = ('username','first_name','last_name','email', 'password1', 'password2')

# Form also for the signup page
class ProfilePageForm(forms.ModelForm):
    class Meta:
        model = UserProfileInfo
        fields = ('nickname', 'gender', 'birth_date', 'address1', 'address2', 'county', 'country', 'prefix', 'phone', 'membership')


class EditProfileForm(UserChangeForm):
    first_name = forms.CharField(max_length=100)
    last_name = forms.CharField(max_length=100)


    class Meta:
        model = get_user_model()
        fields = ('first_name','last_name','email')


class UserCreateForm(UserCreationForm):
    class Meta:
        fields=('email','first_name','last_name', 'password1', 'password2')
        model = get_user_model()


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].label = 'email Address'


class UserProfileInfoForm(forms.ModelForm):
    class Meta:
        model = UserProfileInfo
        fields = [
                'type',
                'active'
            ]
    def __init__(self, *args, **kwargs):
        super(UserProfileInfoForm, self).__init__(*args, **kwargs)
        self.fields['type'].initial = 'USER'
        self.fields['type'].widget = forms.HiddenInput()
        self.fields['active'].initial = 'INACTIVE'
        self.fields['active'].widget = forms.HiddenInput()


class UserUpdateForm(UserCreationForm):

    class Meta:
        fields=['email']
        model = get_user_model()


# Form used so the admin can manage the users
class UserProfileInfoFormUsers(forms.ModelForm):
    class Meta:
        model = UserProfileInfo
        fields = [
                'type',
                'active',
                'nickname',
                'gender',
                'birth_date',
                'address1',
                'address2',
                'county',
                'country',
                'prefix',
                'phone',
            ]
    def __init__(self, *args, **kwargs):
        super(UserProfileInfoFormUsers, self).__init__(*args, **kwargs)
        self.fields['type'].initial = 'USER'
        self.fields['active'].initial = 'INACTIVE'
