from django.conf.urls import url
from ccfit_app import views
from django.contrib.auth import views as auth_views


app_name = 'ccfit'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r"login/$", auth_views.LoginView.as_view(template_name="ccfit_app/login.html"),name='login'),
    url(r"logout/$", auth_views.LogoutView.as_view(), name="logout"),
    #url(r"signup/$", views.SignUp.as_view(), name="signup"),
    url(r"edit_profile/$", views.EditProfile.as_view(), name="edit_profile"),
    url(r"password/$", views.PasswordsChangeView.as_view(template_name='ccfit_app/change_password.html'), name="change_password"),
    url("edit_profile_page/(?P<pk>\d+)", views.EditProfilePageView.as_view(), name="edit_profile_page"),
    url(r"password_sucess/$", views.password_sucess, name="password_sucess"),
    url("create_profile_page/$", views.CreateProfilePageView.as_view(), name="create_profile_page"),
    url(r"booking_page/$", views.BookingPage, name="booking_page"),
    url(r'booking_page/session/', views.Validate_date, name='validates'),
    url(r'workout/$', views.WorkoutView.as_view(), name='workout'),
    url(r'workout/verification/(?P<session>\d)', views.Check_Booking_workout, name='check_booking_workout'),
    url(r'workout/verification/', views.Check_Booking_workout, name='check_booking_workout'),
    url(r'workout/confirmation/', views.Confirmation_Booking, name='confirmation_booking'),
    url(r'pilates/$', views.PilatesView.as_view(), name='pilates'),
    url(r'pilates/verification/(?P<session>\d)', views.Check_Booking_pilates, name='check_booking_pilates'),
    url(r'pilates/verification/', views.Check_Booking_pilates, name='check_booking_pilates'),
    url(r'yoga/$', views.YogaView.as_view(), name='yoga'),
    url(r'yoga/verification/(?P<session>\d)', views.Check_Booking_yoga, name='check_booking_yoga'),
    url(r'yoga/verification/', views.Check_Booking_yoga, name='check_booking_yoga'),
    url(r'spin/$', views.SpinView.as_view(), name='spin'),
    url(r'spin/verification/(?P<session>\d)', views.Check_Booking_spin, name='check_booking_spin'),
    url(r'spin/verification/', views.Check_Booking_spin, name='check_booking_spin'),
    url(r'jump/$', views.JumpView.as_view(), name='jump'),
    url(r'jump/verification/(?P<session>\d)', views.Check_Booking_jump, name='check_booking_jump'),
    url(r'jump/verification/', views.Check_Booking_jump, name='check_booking_jump'),
    url(r"signup/$", views.create_user, name="signup"),
    url(r'allUsers/', views.UsersListView.as_view(), name='all_users'),
    url(r'management/(?P<pk>\d)', views.UsersUpdateView.as_view(), name='update_user'),
    url(r'check_classes/session/', views.Validate_date_check, name='validates_check'),
    url(r"check_classes/$", views.CheckingPage, name="check_classes"),
    url(r'check_classes/change/(?P<class_number>\d)', views.ClassesCountView, name='classes_count'),
    url(r'class/(?P<session>\d)', views.Check_Class_Amount, name='check_class_amount'),
    url(r'my_bookings/', views.MyBookings, name='my_bookings'),

]
