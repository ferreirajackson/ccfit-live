from django import forms
from ccfit_app.models import UserProfileInfo, Workout
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import User

class DateInput(forms.DateInput):
    input_type = 'date'

class ExampleForm(forms.Form):
    my_date_field = forms.DateField(widget=DateInput)

class ExampleModelForm(forms.Form):
    class Meta:
        widgets = {'my_date_field': DateInput()}


class WorkoutForm(forms.ModelForm):

    class Meta:
        model = Workout
        fields = [
                'date',
                'email_user',
                'session_number',
        ]




class SignUpForm(UserCreationForm):
    username = forms.CharField(max_length=50)
    first_name = forms.CharField(max_length=100)
    last_name = forms.CharField(max_length=100)


    class Meta:
        model = get_user_model()
        fields = ('username','first_name','last_name','email', 'password1', 'password2')

class ProfilePageForm(forms.ModelForm):

    class Meta:
        model = UserProfileInfo
        fields = ('nickname', 'gender', 'birth_date', 'address1', 'address2', 'county', 'country', 'prefix', 'phone')


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
        # self.fields['username'].label = 'Display Name'
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
        # self.fields['vendedor'] = self.request.user
        self.fields['type'].initial = 'USER'
        self.fields['type'].widget = forms.HiddenInput()
        self.fields['active'].initial = 'INACTIVE'
        self.fields['active'].widget = forms.HiddenInput()


class UserUpdateForm(UserCreationForm):

    class Meta:
        fields=['email']
        model = get_user_model()


class UserProfileInfoFormUsers(forms.ModelForm):
    class Meta:
        model = UserProfileInfo
        fields = [
                'type',
                'active'
            ]
    def __init__(self, *args, **kwargs):
        super(UserProfileInfoFormUsers, self).__init__(*args, **kwargs)
        # self.fields['vendedor'] = self.request.user
        self.fields['type'].initial = 'USER'
        self.fields['active'].initial = 'INACTIVE'
        #self.fields['type'].widget = forms.HiddenInput()
