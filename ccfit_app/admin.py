from django.contrib import admin
from ccfit_app.models import UserProfileInfo, Workout, Jump, Yoga, Pilates, Spin, MaxSession, Invoice
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import ugettext_lazy as _
from .models import User
# Register your models here.

@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    """Define admin model for custom User model with no email field."""

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )
    list_display = ('email', 'first_name', 'last_name', 'is_staff')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)

# All the tables set here will appear on the django admin panel
admin.site.register(UserProfileInfo)
admin.site.register(Invoice)
admin.site.register(Workout)
admin.site.register(Pilates)
admin.site.register(Spin)
admin.site.register(Yoga)
admin.site.register(Jump)
admin.site.register(MaxSession)
