from django.core.exceptions import PermissionDenied
from .models import UserProfileInfo
from django.http import HttpResponseRedirect
from django.core.exceptions import PermissionDenied
from django.urls import reverse
from django.shortcuts import render
from django.shortcuts import redirect



def user_all_classes(view_func):
    def wrap(request, *args, **kwargs):
        user = UserProfileInfo.objects.filter(email=request.user)
        if user.exists():
            for course in user:
                if course.active == 'WORKOUT ONLY':
                    return render(request, 'ccfit_app/permission_denied.html')
                elif course.active == 'INACTIVE':
                    return render(request, 'ccfit_app/permission_denied.html')
                else:
                    return view_func(request, *args, **kwargs)
        else:
            return view_func(request, *args, **kwargs)
    return wrap

def user_workout(view_func):
    def wrap(request, *args, **kwargs):
        user = UserProfileInfo.objects.filter(email=request.user)
        if user.exists():
            for course in user:
                if course.active == 'ALL CLASSES':
                    return view_func(request, *args, **kwargs)
                elif course.active == 'WORKOUT ONLY':
                    return view_func(request, *args, **kwargs)
                else:
                    return render(request, 'ccfit_app/permission_denied.html')
        else:
            return view_func(request, *args, **kwargs)
    return wrap

def admin_only(view_func):
    def wrap(request, *args, **kwargs):
        user = UserProfileInfo.objects.get(email=request.user)
        if user.type == 'ADMINISTRATOR':
            return view_func(request, *args, **kwargs)
        else:
            return render(request, 'ccfit_app/permission_denied.html')
    return wrap
