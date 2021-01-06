from django.db import models
from django.contrib import auth
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractUser, BaseUserManager ## A new class is imported. ##
from django.utils.translation import ugettext_lazy as _
from django.urls import reverse_lazy


"""Declare models for YOUR_APP app."""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import ugettext_lazy as _


class UserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular User with the given email and password."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """User model."""

    username = None
    email = models.EmailField(_('email address'), unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()



class UserProfileInfo(models.Model):

    TYPE_USER = (
    ('USER','USER'),
    ('TEACHER','TEACHER'),
    )

    ACTIVE = (
    ('INACTIVE','INACTIVE'),
    ('WORKOUT ONLY','WORKOUT ONLY'),
    ('ALL CLASSES','ALL CLASSES'),
    )

    user = models.OneToOneField(User, null=True, on_delete=models.CASCADE)
    email = models.EmailField(max_length=80,null=True)
    name = models.CharField(max_length=50,null=True)
    gender = models.CharField(max_length=50,null=True)
    type = models.CharField(max_length=15, choices = TYPE_USER, null=True)
    active = models.CharField(max_length=15, choices = ACTIVE, null=True)



    def __str__(self):
        return str(self.user)

    def get_absolute_url(self):
        return reverse_lazy('ccfit:index')


class Workout(models.Model):
    date = models.DateField(null=True)
    email_user = models.EmailField(max_length=80,null=True)
    session_number = models.IntegerField(null=True)


    def __str__(self):
        return self.email_user

class Pilates(models.Model):
    date = models.DateField(null=True)
    email_user = models.EmailField(max_length=80,null=True)
    session_number = models.IntegerField(null=True)


    def __str__(self):
        return self.email_user

    def test(self):
        return 'Pilates'


class Yoga(models.Model):
    date = models.DateField(null=True)
    email_user = models.EmailField(max_length=80,null=True)
    session_number = models.IntegerField(null=True)


    def __str__(self):
        return self.email_user

class Jump(models.Model):
    date = models.DateField(null=True)
    email_user = models.EmailField(max_length=80,null=True)
    session_number = models.IntegerField(null=True)


    def __str__(self):
        return self.email_user

class Spin(models.Model):
    date = models.DateField(null=True)
    email_user = models.EmailField(max_length=80,null=True)
    session_number = models.IntegerField(null=True)


    def __str__(self):
        return self.email_user
