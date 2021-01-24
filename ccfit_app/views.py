from django.shortcuts import render, redirect, get_object_or_404, redirect
from .models import Workout, UserProfileInfo, Pilates, Yoga, Spin, Jump, User, MaxSession, Invoice
from django.contrib.auth.decorators import login_required
from . import forms
from django.views import generic
from ccfit_app.forms import SignUpForm, EditProfileForm, ProfilePageForm, ExampleForm, UserProfileInfoForm, UserCreateForm, UserUpdateForm, UserProfileInfoFormUsers
from django.contrib.auth import login, logout, authenticate, login
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, PasswordChangeForm
from django.urls import reverse_lazy, reverse
from django.contrib.auth.views import PasswordChangeView
from django.views.generic import CreateView, UpdateView, TemplateView, ListView, View
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from datetime import datetime, timedelta
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import send_mail
from .decorators import user_all_classes, user_workout, admin_only, admin_teacher_only
from django.utils.decorators import method_decorator
from django.template.loader import get_template
from django.contrib.staticfiles import finders
from xhtml2pdf import pisa
from django.conf import settings
import stripe
import time
import os


# Down below are all the functions and classes where the
# logic for the whole website is kept


# stripe.api_key = os.environ.get('STRIPE_PRIVATE_KEY')
stripe.api_key = 'sk_test_51I8CofKwMtRnc3TERmC6RgEX2KX4okNeqmnHVAZwu0wCva0SewBG1x6BJ5yOpPik2qct0yNaewqrLNerI7oQbdLf00Oyz3Ulph'


# Function responsible process the payment wheather is
# and enrollment fee or monthly payment
@login_required
def Payment_request(request):
	# Enrollment fee
	if request.session['type_payment'] == '1':
		amount = 30
		description = 'enrolment fee'
	else:
		# Monthly payment
		user = UserProfileInfo.objects.get(email=request.user)
		if user.active == 'ALL CLASSES':
			amount = 50
		elif user.active == 'WORKOUT ONLY':
			amount = 35
		else:
		    print('Inactive User')
		description = 'monthly payment'

	# Executed when the submit is pressed
	if request.method == 'POST':
		customer = stripe.Customer.create(
			email=request.POST['email'],
			name=request.POST['nickname'],
			source=request.POST['stripeToken']
		)
		charge = stripe.Charge.create(
			customer=customer,
			amount=amount*100,
			currency='eur',
			description=description,
		)

		#Updating status and data for that users payment
		if request.session['type_payment'] == '1':
			verify_enrollment = Invoice.objects.get(email=request.user, type='ENROLMENT FEE')
			today_date = datetime.today().strftime('%Y-%m-%d')
			today_date_object = datetime.strptime(today_date, '%Y-%m-%d').date()
			future_30days = str(today_date_object + timedelta(days = 30))
			future_30days_DATE = datetime.strptime(future_30days, '%Y-%m-%d').date()
			verify_enrollment.from_date = today_date_object
			verify_enrollment.to_date = future_30days_DATE
			verify_enrollment.status = 'PAID'
			verify_enrollment.save()
			email_user = str(request.user)
			message = 'Dear ' + str(verify_enrollment.email) + '\nThank you for trusting CCFIT to be your gym. \nThis is your receipt for paying €' +  str(verify_enrollment.cost) + ' regarding the ' + verify_enrollment.type
			send_mail('CCFIT Invoice: ' + str(verify_enrollment.from_date) + ' - ' + str(verify_enrollment.to_date), message, 'ccfitgym@gmail.com', [email_user], fail_silently=False)
		else:
			# this if is for the monthly payment
			verify_enrollment = Invoice.objects.filter(email=request.user, type='MONTHLY PAYMENT', status='REQUESTED').order_by('from_date')
			if verify_enrollment.exists():
				for course in verify_enrollment:
					verify_enrollment_unique = Invoice.objects.get(pk=course.pk)
					verify_enrollment_unique.status = 'PAID'
					verify_enrollment_unique.save()
					email_user = str(request.user)
					message = 'Dear ' + str(verify_enrollment_unique.email) + '\nThank you for trusting CCFIT to be your gym. \nThis is your receipt for paying €' +  str(verify_enrollment_unique.cost) + ' regarding the ' + verify_enrollment_unique.type
					send_mail('CCFIT Invoice: ' + str(verify_enrollment_unique.from_date) + ' - ' + str(verify_enrollment_unique.to_date), message, 'ccfitgym@gmail.com', [email_user], fail_silently=False)
					break
	request.session['confirm_message'] = 'PAID'
	return HttpResponseRedirect(reverse_lazy('ccfit:index'))
	# return render(request, 'ccfit_app/index.html')


# Function for the button in the generate invoice page
# to mark the payment as paid when the user doesnt pay
# by stripe
@login_required
@admin_only
def MarkPaid(request, pk):
	verify_enrollment = Invoice.objects.get(pk=pk)
	verify_enrollment.status = 'PAID'
	verify_enrollment.save()
	return HttpResponseRedirect(reverse_lazy('ccfit:invoices'))


# Function for the button in the generate invoice page
# send the invoice to the user when generated
@login_required
@admin_only
def SendInvoice(request, pk):
	verify_enrollment = Invoice.objects.get(pk=pk)
	verify_enrollment.status = 'REQUESTED'
	verify_enrollment.save()
	email_user = str(verify_enrollment.email)
	message = 'Dear ' + str(verify_enrollment.email) + '\nThank you for trusting CCFIT to be your gym. \nYour invoice for this month is now availabe.' + ' \nCheck on https://ccfitgym.herokuapp.com/ to pay'
	# Send email
	send_mail('CCFIT Invoice: ' + str(verify_enrollment.from_date) + ' - ' + str(verify_enrollment.to_date), message, 'ccfitgym@gmail.com', [email_user], fail_silently=False)
	return HttpResponseRedirect(reverse_lazy('ccfit:invoices'))

# Funcion that processes the payment and
# shows the info for the user before paying
@login_required
def Payment(request, type):
	request.session['confirm_message'] = ''
	request.session['type_payment'] = type
	user = UserProfileInfo.objects.get(email=request.user)
	# Checking if is enrollment fee or montly payment
	if request.session['type_payment'] == '1':
		description = 'ENROLMENT FEE'
		invoice = Invoice.objects.get(email=request.user, type='ENROLMENT FEE')
		from_date = invoice.from_date
		to_date = invoice.to_date
		year = invoice.year
		cost = invoice.cost
		pk = invoice.pk
	else:
		# If for the monthly payment
		description = 'MONTHLY PAYMENT'
		invoice = Invoice.objects.filter(email=request.user, type='MONTHLY PAYMENT', status='REQUESTED').order_by('from_date')
		if invoice.exists():
			for course in invoice:
				from_date = course.from_date
				to_date = course.to_date
				year = course.year
				cost = course.cost
				pk = course.pk
				break
	context = {'pk': pk, 'nickname':user.nickname, 'email': request.user, 'from_date':from_date, 'to_date': to_date, 'cost':cost,'subscription':description, 'year':year }
	return render(request, 'ccfit_app/payment.html', context)


# Invoice page
@method_decorator(admin_only, name='dispatch')
class InvoiceListView(LoginRequiredMixin, ListView):
	template_name = "ccfit_app/invoices.html"
	model = Invoice
	context_object_name = "invoices"


	def get_queryset(self):
		print("FAZ A BUSCA PADRAO DO FILTRO")
		email = self.request.GET.get('search')
		print(email, 'thats the email')
		object_list = self.model.objects.all()
		print(object_list)
		if email:
			object_list = object_list.filter(email__contains=email)
		return object_list


# This function allows the functions of creation of the pdf
# to have images and other resources
def link_callback(uri, rel):
        result = finders.find(uri)
        if result:
                if not isinstance(result, (list, tuple)):
                        result = [result]
                result = list(os.path.realpath(path) for path in result)
                path=result[0]
        else:
                sUrl = settings.STATIC_URL        # Typically /static/
                sRoot = settings.STATIC_ROOT      # Typically /home/userX/project_static/
                mUrl = settings.MEDIA_URL         # Typically /media/
                mRoot = settings.MEDIA_ROOT       # Typically /home/userX/project_static/media/

                if uri.startswith(mUrl):
                        path = os.path.join(mRoot, uri.replace(mUrl, ""))
                elif uri.startswith(sUrl):
                        path = os.path.join(sRoot, uri.replace(sUrl, ""))
                else:
                        return uri

        # make sure that file exists
        if not os.path.isfile(path):
                raise Exception(
                        'media URI must start with %s or %s' % (sUrl, mUrl)
                )
        return path

# Main function that creates the pdf
def render_to_pdf(template_src, context_dict={}):
	template = get_template(template_src)
	html  = template.render(context_dict)
	response = HttpResponse(content_type='application/pdf')
	response['Content-Disposition'] = 'filename="Invoice.pdf"'
	pisa_status = pisa.CreatePDF(html, dest=response, link_callback=link_callback)
	if pisa_status.err:
		return HttpResponse('we had some erros')
	return response


# Function that calls the main function from the generate invoice
class InvoiceUser(LoginRequiredMixin, View):
	def get(self, request, *args, **kwargs):
		new = Invoice.objects.filter(pk=self.kwargs['pk'])
		if new.exists():
			for unit in new:
				user = UserProfileInfo.objects.get(email=unit.email)
				d1 = {'email': unit.email, 'from_date': str(unit.from_date), 'to_date': str(unit.to_date),
						'cost': unit.cost, 'type': unit.type, 'subscription': user.active,
						'nickname': user.nickname, 'gender': user.gender, 'address_one': user.address1,
						'address_two': user.address2, 'county': user.county, 'country': user.country,
						 'prefix': user.prefix, 'phone': user.phone}
		# Calls the main function to create the pdf
		pdf = render_to_pdf('ccfit_app/pdf/invoice_template.html', d1)
		response = HttpResponse(pdf, content_type='application/pdf')
		content = 'filename="report.pdf"'
		response['Content-Disposition'] = content
		return response


# Function that calls the main function from the check_classes
class PDF(LoginRequiredMixin, View):
	def get(self, request, *args, **kwargs):
		dict = {'1': Workout,'2': Pilates,'3': Jump,'4': Spin,'5': Yoga}
		class_number = str(request.session['class'])
		print(class_number)
		list = [1,2,3,4,5,6]
		list_user = []
		data_second, major = {},{}
		for num in list:
			new = dict[class_number].objects.filter(date=request.session['value'], session_number=num)
			# Generating the pdf for the check_classes
			if new.exists():
				for unit in new:
					user = UserProfileInfo.objects.get(email=unit.email_user)
					list_user.extend((user.nickname, user.phone))
					first_dict = {unit.email_user: list_user}
					major.update(first_dict)
					list_user = []
				sessions = {'1': 'from 06:00 to 08:00','2': 'from 09:00 to 11:00','3': 'from 12:00 to 14:00','4': 'from 15:00 to 17:00','5': 'from 18:00 to 20:00', '6': 'from 21:00 to 23:00'}
				d1 = {sessions[str(num)]: major}
				data_second.update(d1)
				major = {}

		context = {"work" : Workout.objects.filter(date=self.request.session['value']).order_by('session_number')}
		print(data_second)
		pdf = render_to_pdf('ccfit_app/pdf/pdf_template.html', {'data': data_second})

		return HttpResponse(pdf, content_type='application/pdf')



# Function that download the pdf provided
class DownloadPDF(LoginRequiredMixin, View):
	def get(self, request, *args, **kwargs):
		dict = {'1': Workout,'2': Pilates,'3': Jump,'4': Spin,'5': Yoga}
		class_number = str(request.session['class'])
		list = [1,2,3,4,5,6]
		list_user = []
		data_second, major = {},{}
		for num in list:
			new = dict[class_number].objects.filter(date=request.session['value'], session_number=num)
			if new.exists():
				for unit in new:
					user = UserProfileInfo.objects.get(email=unit.email_user)
					list_user.extend((user.nickname, user.phone))
					first_dict = {unit.email_user: list_user}
					major.update(first_dict)
					list_user = []
				d1 = {str(num): major}
				data_second.update(d1)
				major = {}
		context = {"work" : Workout.objects.filter(date=self.request.session['value']).order_by('session_number')}
		pdf = render_to_pdf('ccfit_app/pdf/pdf_template.html', {'data': data_second})
		response = HttpResponse(pdf, content_type='application/pdf')
		# This next line makes the download
		content = 'attachment; filename="'+ str(request.session['value']) + '.pdf"'
		response['Content-Disposition'] = content
		return response


# Confirmation screen
@login_required
def Confirmation_Booking(request, n1):
    return render(request, 'ccfit_app/confirmation.html', context)


# Process all the bookings for each user since the first class
@login_required
def MyBookings(request):
    request.session['confirm_message'] = ''
    models = [Workout, Pilates, Spin, Yoga, Jump]
    data, new = {}, {}
    sessions = {'1': 'from 06:00 to 08:00','2': 'from 09:00 to 11:00','3': 'from 12:00 to 14:00','4': 'from 15:00 to 17:00','5': 'from 18:00 to 20:00', '6': 'from 21:00 to 23:00'}
    for model in models:
		# Checks all the tables and retrieves all the class for that user
        found_booking = model.objects.filter(email_user=request.user)
        if found_booking.exists():
            for unit in found_booking:
                d1 = {str(unit.date): [str(request.user), sessions[str(unit.session_number)], model.__name__]}
                data.update(d1)
    for key in sorted(data):
        new[key] = data[key]
    return render(request, 'ccfit_app/my_bookings.html', {'data': new})


# Function that validates the date
# for the booking session
@login_required
@admin_teacher_only
def Validate_date_check(request):
    if request.is_ajax():
        global date
        date  = request.POST.get('date_verification')
        request.session['value'] = date
        name_dict = \
                            {
                                'workout': 'false',
                                'pilates': 'false',
                                'spin': 'false',
                                'jump': 'false',
                                'yoga': 'false',
                             }
        return JsonResponse(name_dict)
    return render(request, 'ccfit_app/check_classes.html')


# Function that validates the date
# for the check classes
@login_required
def Validate_date(request):
    if request.is_ajax():
        global date
        date  = request.POST.get('date_verification')
        request.session['value'] = date
        user = UserProfileInfo.objects.filter(email=request.user)
        name_dict = \
                            {'workout': 'false','pilates': 'false','spin': 'false','jump': 'false','yoga': 'false',}
        if user.exists():
            for course in user:
                if course.active == 'WORKOUT ONLY':
                    name_dict = \
                            {'workout': 'false','pilates': 'true','spin': 'true','jump': 'true','yoga': 'true',}
                elif course.active == 'INACTIVE':
                    name_dict = \
                            {'workout': 'true','pilates': 'true','spin': 'true','jump': 'true','yoga': 'true',}
        return JsonResponse(name_dict)
    return render(request, 'ccfit_app/booking_page.html')


# Displays the users in the screen
@login_required
def Check_Class_Amount(request, session):
    cancel = User.objects.filter(email=request.user)
    if cancel.exists():
        context, data = {}, {}
        list = []
        class_name = request.session['class']
        dict = {'1': Workout,'2': Pilates,'3': Jump,'4': Spin,'5': Yoga}
		# Brings all the users per session according to the
		# day provided
        new = dict[class_name].objects.filter(date=request.session['value'], session_number=session)
        if new.exists():
            for unit in new:
                list.append(unit.email_user)
                user = UserProfileInfo.objects.get(email=unit.email_user)
                d1 = {str(unit.email_user): [user.nickname, user.active]}
                data.update(d1)
        return render(request, 'ccfit_app/class_amount.html', {'data': data})


# Displays the amount the users per session
@login_required
@admin_teacher_only
def ClassesCountView(request, class_number):
    cancel = User.objects.filter(email=request.user)
    if cancel.exists():
        dict = {'1': Workout,'2': Pilates,'3': Jump,'4': Spin,'5': Yoga}
        # list = [1,2,3,4,5,6]
        request.session['class'] = class_number
        context = {'session_1': {'start':'06:00', 'finish':'08:00', 'session_number': 1, '1': 0, 'enable':False},
                'session_2': { 'start':'09:00', 'finish':'11:00', 'session_number': 2, '2': 0, 'enable':False},
                'session_3': { 'start':'12:00', 'finish':'14:00', 'session_number': 3, '3': 0, 'enable':False},
                'session_4': { 'start':'15:00', 'finish':'17:00', 'session_number': 4, '4': 0, 'enable':False},
                'session_5': { 'start':'18:00', 'finish':'20:00', 'session_number': 5, '5': 0, 'enable':False},
                'session_6': { 'start':'21:00', 'finish':'23:00', 'session_number': 6, '6': 0, 'enable':False}}
        found_booking = dict[class_number].objects.filter(date=request.session['value']).values('session_number')
        show_buttons = False
        if found_booking.exists():
            for unit in found_booking:
                session_number_keep = unit['session_number']
                session_number_keep = str(session_number_keep)
                session_id = 'session_' + session_number_keep
                context[session_id][session_number_keep] += 1
                if context[session_id]['enable'] == False:
                    context[session_id]['enable'] = True
                    show_buttons = True
            dict = {'show_buttons': show_buttons}
            context.update(dict)
    return render(request, 'ccfit_app/count_classes.html', context)

# Workout view
@method_decorator(user_workout, name='dispatch')
class WorkoutView(LoginRequiredMixin, generic.TemplateView):
    model = Workout
    template_name = "ccfit_app/workout.html"

    def get_context_data(self, **kwargs):
        context = super(WorkoutView, self).get_context_data(**kwargs)
        booked_flag = 'N'

        if 'value' in self.request.session:
            booking_date = self.request.session['value']

            #BOOKING DATE
            booking_date_object = datetime.strptime(booking_date, '%Y-%m-%d').date()

            #TODAY'S DATE
            today_date = datetime.today().strftime('%Y-%m-%d')
            today_date_object = datetime.strptime(today_date, '%Y-%m-%d').date()
            context = {'session_1': {'start':'06:00', 'finish':'08:00', 'session_number': 1, 'expired':True,'status':'BOOK', 'enable':False},
                    'session_2': { 'start':'09:00', 'finish':'11:00', 'session_number': 2,  'expired':True, 'status':'BOOK', 'enable':False},
                    'session_3': { 'start':'12:00', 'finish':'14:00', 'session_number': 3,  'expired':True, 'status':'BOOK', 'enable':False},
                    'session_4': { 'start':'15:00', 'finish':'17:00', 'session_number': 4,  'expired':True, 'status':'BOOK', 'enable':False},
                    'session_5': { 'start':'18:00', 'finish':'20:00', 'session_number': 5,  'expired':True, 'status':'BOOK', 'enable':False},
                    'session_6': { 'start':'21:00', 'finish':'23:00', 'session_number': 6,  'expired':True, 'status':'BOOK', 'enable':False}}

            # IF HERE TO CHECK IF THERE IS ALREADY A BOOKING FOR THIS DAY
            user = Workout.objects.filter(email_user=self.request.user, date=self.request.session['value']).values('session_number')
            if user.exists():
                booked_flag = 'Y'
                for course in user:
                    session_number_keep = course['session_number']

            if booking_date_object == today_date_object:
                #do something
                start_hour = time.strftime("%H")
                start_minute = time.strftime("%M")

                for key in context:
                    schedule_date = context[key]['start']

                    start_time = (int(schedule_date[0:2])*60 + int(schedule_date[3:5])-30)
                    current_time =  datetime.now().hour*60 +datetime.now().minute
                    if start_time <= current_time:
                        context[key]['expired'] = False

                    #Getting the number max of users per session and class from table MaxSession model
                    num_max_users = MaxSession.objects.filter(key='CCFIT')
                    for number in num_max_users:
                        #DO THE LOGIC TO CONTROL THE AMOUNT OF USERS
                        count = Workout.objects.filter(date=self.request.session['value'], session_number=context[key]['session_number']).count()
                        if count == number.workout:
                            context[key]['status'] = 'FULLY BOOKED'
                            context[key]['enable'] = True

            elif booking_date_object < today_date_object:
                for key in context:
                    context[key]['expired'] = False
                #return to the user that
            else:
                for key in context:
                    #Getting the number max of users per session and class from table MaxSession model
                    num_max_users = MaxSession.objects.filter(key='CCFIT')
                    for number in num_max_users:
                        #DO THE LOGIC TO CONTROL THE AMOUNT OF USERS
                        count = Workout.objects.filter(date=self.request.session['value'], session_number=context[key]['session_number']).count()
                        if count == number.workout:
                            context[key]['status'] = 'FULLY BOOKED'
                            context[key]['enable'] = True

            if booked_flag == 'Y':
                for key in context:

                    #enabling the cancelling for users that have booked and the class is fully booked
                    context[key]['enable'] = False

                    if context[key]['session_number'] == session_number_keep:
                        context[key]['status'] = 'CANCEL'
                    else:
                        context[key]['enable'] = True

            dict = {'date': booking_date}
            context.update(dict)

        return context


# Pilates view
@method_decorator(user_all_classes, name='dispatch')
class PilatesView(LoginRequiredMixin, generic.TemplateView):
    model = Pilates
    template_name = "ccfit_app/pilates.html"

    def get_context_data(self, **kwargs):
        context = super(PilatesView, self).get_context_data(**kwargs)
        booked_flag = 'N'

        if 'value' in self.request.session:
            booking_date = self.request.session['value']

            #BOOKING DATE
            booking_date_object = datetime.strptime(booking_date, '%Y-%m-%d').date()
            #TODAY'S DATE
            today_date = datetime.today().strftime('%Y-%m-%d')
            today_date_object = datetime.strptime(today_date, '%Y-%m-%d').date()
            context = {'session_1': {'start':'06:00', 'finish':'08:00', 'session_number': 1, 'expired':True,'status':'BOOK', 'enable':False},
                    'session_2': { 'start':'09:00', 'finish':'11:00', 'session_number': 2,  'expired':True, 'status':'BOOK', 'enable':False},
                    'session_3': { 'start':'12:00', 'finish':'14:00', 'session_number': 3,  'expired':True, 'status':'BOOK', 'enable':False},
                    'session_4': { 'start':'15:00', 'finish':'17:00', 'session_number': 4,  'expired':True, 'status':'BOOK', 'enable':False},
                    'session_5': { 'start':'18:00', 'finish':'20:00', 'session_number': 5,  'expired':True, 'status':'BOOK', 'enable':False},
                    'session_6': { 'start':'21:00', 'finish':'23:00', 'session_number': 6,  'expired':True, 'status':'BOOK', 'enable':False}}

            # IF HERE TO CHECK IF THERE IS ALREADY A BOOKING FOR THIS DAY
            user = Pilates.objects.filter(email_user=self.request.user, date=self.request.session['value']).values('session_number')
            if user.exists():
                booked_flag = 'Y'
                for course in user:
                    session_number_keep = course['session_number']
            if booking_date_object == today_date_object:
                #do something
                start_hour = time.strftime("%H")
                start_minute = time.strftime("%M")

                for key in context:
                    schedule_date = context[key]['start']

                    start_time = (int(schedule_date[0:2])*60 + int(schedule_date[3:5])-30)
                    current_time =  datetime.now().hour*60 +datetime.now().minute
                    if start_time <= current_time:
                        context[key]['expired'] = False

                    #Getting the number max of users per session and class from table MaxSession model
                    num_max_users = MaxSession.objects.filter(key='CCFIT')
                    for number in num_max_users:
                        #DO THE LOGIC TO CONTROL THE AMOUNT OF USERS
                        count = Pilates.objects.filter(date=self.request.session['value'], session_number=context[key]['session_number']).count()
                        if count == number.pilates:
                            context[key]['enable'] = True


            elif booking_date_object < today_date_object:
                for key in context:
                    context[key]['expired'] = False
                #return to the user that
            else:
                for key in context:
                    #Getting the number max of users per session and class from table MaxSession model
                    num_max_users = MaxSession.objects.filter(key='CCFIT')
                    for number in num_max_users:

                        #DO THE LOGIC TO CONTROL THE AMOUNT OF USERS
                        count = Pilates.objects.filter(date=self.request.session['value'], session_number=context[key]['session_number']).count()
                        if count == number.pilates:
                            context[key]['status'] = 'FULLY BOOKED'
                            context[key]['enable'] = True

            if booked_flag == 'Y':
                for key in context:

                    #enabling the cancelling for users that have booked and the class is fully booked
                    context[key]['enable'] = False

                    if context[key]['session_number'] == session_number_keep:
                        context[key]['status'] = 'CANCEL'
                    else:
                        context[key]['enable'] = True

            dict = {'date': booking_date}
            context.update(dict)

        return context


# Yoga view
@method_decorator(user_all_classes, name='dispatch')
class YogaView(LoginRequiredMixin, generic.TemplateView):
    model = Yoga
    template_name = "ccfit_app/yoga.html"

    def get_context_data(self, **kwargs):
        context = super(YogaView, self).get_context_data(**kwargs)
        booked_flag = 'N'

        if 'value' in self.request.session:
            booking_date = self.request.session['value']

            #BOOKING DATE
            booking_date_object = datetime.strptime(booking_date, '%Y-%m-%d').date()
            #TODAY'S DATE
            today_date = datetime.today().strftime('%Y-%m-%d')
            today_date_object = datetime.strptime(today_date, '%Y-%m-%d').date()
            context = {'session_1': {'start':'06:00', 'finish':'08:00', 'session_number': 1, 'expired':True,'status':'BOOK', 'enable':False},
                    'session_2': { 'start':'09:00', 'finish':'11:00', 'session_number': 2,  'expired':True, 'status':'BOOK', 'enable':False},
                    'session_3': { 'start':'12:00', 'finish':'14:00', 'session_number': 3,  'expired':True, 'status':'BOOK', 'enable':False},
                    'session_4': { 'start':'15:00', 'finish':'17:00', 'session_number': 4,  'expired':True, 'status':'BOOK', 'enable':False},
                    'session_5': { 'start':'18:00', 'finish':'20:00', 'session_number': 5,  'expired':True, 'status':'BOOK', 'enable':False},
                    'session_6': { 'start':'21:00', 'finish':'23:00', 'session_number': 6,  'expired':True, 'status':'BOOK', 'enable':False}}

            # IF HERE TO CHECK IF THERE IS ALREADY A BOOKING FOR THIS DAY
            user = Yoga.objects.filter(email_user=self.request.user, date=self.request.session['value']).values('session_number')
            if user.exists():
                booked_flag = 'Y'
                for course in user:
                    session_number_keep = course['session_number']
            #---------------------------------------------------------------------
            #---------------------------------------------------------------------
            if booking_date_object == today_date_object:
                #do something
                start_hour = time.strftime("%H")
                start_minute = time.strftime("%M")

                for key in context:
                    schedule_date = context[key]['start']

                    start_time = (int(schedule_date[0:2])*60 + int(schedule_date[3:5])-30)
                    current_time =  datetime.now().hour*60 +datetime.now().minute
                    if start_time <= current_time:
                        context[key]['expired'] = False

                    #Getting the number max of users per session and class from table MaxSession model
                    num_max_users = MaxSession.objects.filter(key='CCFIT')
                    for number in num_max_users:

                        #DO THE LOGIC TO CONTROL THE AMOUNT OF USERS
                        count = Yoga.objects.filter(date=self.request.session['value'], session_number=context[key]['session_number']).count()
                        if count == number.yoga:
                            context[key]['status'] = 'FULLY BOOKED'
                            context[key]['enable'] = True

            elif booking_date_object < today_date_object:
                for key in context:
                    context[key]['expired'] = False
                #return to the user that
            else:
                for key in context:
                    #DO THE LOGIC TO CONTROL THE AMOUNT OF USERS
                    #Getting the number max of users per session and class from table MaxSession model
                    num_max_users = MaxSession.objects.filter(key='CCFIT')
                    for number in num_max_users:

                        count = Yoga.objects.filter(date=self.request.session['value'], session_number=context[key]['session_number']).count()
                        if count == number.yoga:
                            context[key]['status'] = 'FULLY BOOKED'
                            context[key]['enable'] = True

            if booked_flag == 'Y':
                for key in context:

                    #enabling the cancelling for users that have booked and the class is fully booked
                    context[key]['enable'] = False

                    if context[key]['session_number'] == session_number_keep:
                        context[key]['status'] = 'CANCEL'
                    else:
                        context[key]['enable'] = True

            dict = {'date': booking_date}
            context.update(dict)

        return context


# Spin view
@method_decorator(user_all_classes, name='dispatch')
class SpinView(LoginRequiredMixin, generic.TemplateView):
    model = Spin
    template_name = "ccfit_app/spin.html"

    def get_context_data(self, **kwargs):
        context = super(SpinView, self).get_context_data(**kwargs)
        booked_flag = 'N'
        if 'value' in self.request.session:
            booking_date = self.request.session['value']
            #BOOKING DATE
            booking_date_object = datetime.strptime(booking_date, '%Y-%m-%d').date()
            #TODAY'S DATE
            today_date = datetime.today().strftime('%Y-%m-%d')
            today_date_object = datetime.strptime(today_date, '%Y-%m-%d').date()
            context = {'session_1': {'start':'06:00', 'finish':'08:00', 'session_number': 1, 'expired':True,'status':'BOOK', 'enable':False},
                    'session_2': { 'start':'09:00', 'finish':'11:00', 'session_number': 2,  'expired':True, 'status':'BOOK', 'enable':False},
                    'session_3': { 'start':'12:00', 'finish':'14:00', 'session_number': 3,  'expired':True, 'status':'BOOK', 'enable':False},
                    'session_4': { 'start':'15:00', 'finish':'17:00', 'session_number': 4,  'expired':True, 'status':'BOOK', 'enable':False},
                    'session_5': { 'start':'18:00', 'finish':'20:00', 'session_number': 5,  'expired':True, 'status':'BOOK', 'enable':False},
                    'session_6': { 'start':'21:00', 'finish':'23:00', 'session_number': 6,  'expired':True, 'status':'BOOK', 'enable':False}}
            # IF HERE TO CHECK IF THERE IS ALREADY A BOOKING FOR THIS DAY
            user = Spin.objects.filter(email_user=self.request.user, date=self.request.session['value']).values('session_number')
            if user.exists():
                booked_flag = 'Y'
                for course in user:
                    session_number_keep = course['session_number']
            if booking_date_object == today_date_object:
                #do something
                start_hour = time.strftime("%H")
                start_minute = time.strftime("%M")
                for key in context:
                    schedule_date = context[key]['start']
                    start_time = (int(schedule_date[0:2])*60 + int(schedule_date[3:5])-30)
                    current_time =  datetime.now().hour*60 +datetime.now().minute
                    if start_time <= current_time:
                        context[key]['expired'] = False

                    #Getting the number max of users per session and class from table MaxSession model
                    num_max_users = MaxSession.objects.filter(key='CCFIT')
                    for number in num_max_users:

                        #DO THE LOGIC TO CONTROL THE AMOUNT OF USERS
                        count = Spin.objects.filter(date=self.request.session['value'], session_number=context[key]['session_number']).count()
                        if count == number.spin:
                            context[key]['status'] = 'FULLY BOOKED'
                            context[key]['enable'] = True
            elif booking_date_object < today_date_object:
                for key in context:
                    context[key]['expired'] = False
                #return to the user that
            else:
                for key in context:
                    #DO THE LOGIC TO CONTROL THE AMOUNT OF USERS
                    #Getting the number max of users per session and class from table MaxSession model
                    num_max_users = MaxSession.objects.filter(key='CCFIT')
                    for number in num_max_users:

                        count = Spin.objects.filter(date=self.request.session['value'], session_number=context[key]['session_number']).count()
                        if count == number.spin:
                            context[key]['status'] = 'FULLY BOOKED'
                            context[key]['enable'] = True

            if booked_flag == 'Y':
                for key in context:

                    #enabling the cancelling for users that have booked and the class is fully booked
                    context[key]['enable'] = False

                    if context[key]['session_number'] == session_number_keep:
                        context[key]['status'] = 'CANCEL'
                    else:
                        context[key]['enable'] = True

            dict = {'date': booking_date}
            context.update(dict)

        return context


# Jump view
@method_decorator(user_all_classes, name='dispatch')
class JumpView(LoginRequiredMixin, generic.TemplateView):
    model = Jump
    template_name = "ccfit_app/jump.html"

    def get_context_data(self, **kwargs):
        context = super(JumpView, self).get_context_data(**kwargs)
        booked_flag = 'N'

        if 'value' in self.request.session:
            booking_date = self.request.session['value']

            #BOOKING DATE
            booking_date_object = datetime.strptime(booking_date, '%Y-%m-%d').date()
            #TODAY'S DATE
            today_date = datetime.today().strftime('%Y-%m-%d')
            today_date_object = datetime.strptime(today_date, '%Y-%m-%d').date()
            context = {'session_1': {'start':'06:00', 'finish':'08:00', 'session_number': 1, 'expired':True,'status':'BOOK', 'enable':False},
                    'session_2': { 'start':'09:00', 'finish':'11:00', 'session_number': 2,  'expired':True, 'status':'BOOK', 'enable':False},
                    'session_3': { 'start':'12:00', 'finish':'14:00', 'session_number': 3,  'expired':True, 'status':'BOOK', 'enable':False},
                    'session_4': { 'start':'15:00', 'finish':'17:00', 'session_number': 4,  'expired':True, 'status':'BOOK', 'enable':False},
                    'session_5': { 'start':'18:00', 'finish':'20:00', 'session_number': 5,  'expired':True, 'status':'BOOK', 'enable':False},
                    'session_6': { 'start':'21:00', 'finish':'23:00', 'session_number': 6,  'expired':True, 'status':'BOOK', 'enable':False}}
            # IF HERE TO CHECK IF THERE IS ALREADY A BOOKING FOR THIS DAY
            user = Jump.objects.filter(email_user=self.request.user, date=self.request.session['value']).values('session_number')
            if user.exists():
                booked_flag = 'Y'
                for course in user:
                    session_number_keep = course['session_number']
            if booking_date_object == today_date_object:
                #do something
                start_hour = time.strftime("%H")
                start_minute = time.strftime("%M")
                for key in context:
                    schedule_date = context[key]['start']
                    start_time = (int(schedule_date[0:2])*60 + int(schedule_date[3:5])-30)
                    current_time =  datetime.now().hour*60 +datetime.now().minute
                    if start_time <= current_time:
                        context[key]['expired'] = False
                    #DO THE LOGIC TO CONTROL THE AMOUNT OF USERS
                    #Getting the number max of users per session and class from table MaxSession model
                    num_max_users = MaxSession.objects.filter(key='CCFIT')
                    for number in num_max_users:

                        count = Jump.objects.filter(date=self.request.session['value'], session_number=context[key]['session_number']).count()
                        if count == number.jump:
                            context[key]['status'] = 'FULLY BOOKED'
                            context[key]['enable'] = True
            elif booking_date_object < today_date_object:
                for key in context:
                    context[key]['expired'] = False
                #return to the user that
            else:
                for key in context:
                    #DO THE LOGIC TO CONTROL THE AMOUNT OF USERS
                    #Getting the number max of users per session and class from table MaxSession model
                    num_max_users = MaxSession.objects.filter(key='CCFIT')
                    for number in num_max_users:

                        count = Jump.objects.filter(date=self.request.session['value'], session_number=context[key]['session_number']).count()
                        if count == number.jump:
                            context[key]['status'] = 'FULLY BOOKED'
                            context[key]['enable'] = True
            if booked_flag == 'Y':
                for key in context:
                    #enabling the cancelling for users that have booked and the class is fully booked
                    context[key]['enable'] = False

                    if context[key]['session_number'] == session_number_keep:
                        context[key]['status'] = 'CANCEL'
                    else:
                        context[key]['enable'] = True
            dict = {'date': booking_date}
            context.update(dict)
        return context


# Function that checks if all the classes are
# cancelled and deletes the invoice if so
def cancelling_allclases(request):
    program_date = datetime.strptime(request.session['value'], '%Y-%m-%d').date()
    invoice = Invoice.objects.get(email=request.user, from_date__lte=program_date, to_date__gte=program_date, type="MONTHLY PAYMENT")
    models = [Workout, Pilates, Spin, Yoga, Jump]
	# checking all the tables
    found_other_bookings = True
    for model in models:
        number_bookings = model.objects.filter(email_user=request.user, date__gte=invoice.from_date)
        if number_bookings.exists():
            number_bookings = model.objects.filter(email_user=request.user, date__lte=invoice.to_date)
            if number_bookings.exists():
                found_other_bookings = False
                break
    if found_other_bookings == True:
        invoice.delete()

# Inserts the invoice in the table
def invoice_insertion(request):
	#Do the invoice insertion
	verify_enrollment = Invoice.objects.filter(email=request.user, type='MONTHLY PAYMENT')
	if not verify_enrollment.exists():
		user = UserProfileInfo.objects.get(email=request.user)
		cost = 35
		if user.active == 'WORKOUT ONLY':
			cost = 35
		else:
			cost = 50
		verify = Invoice.objects.get(email=request.user, type='ENROLMENT FEE')
		today_date = datetime.today().strftime('%Y-%m-%d')
		today_date_audit = datetime.strptime(today_date, '%Y-%m-%d').date()
		time = datetime.today().strftime('%H:%M:%S')
		time_audit = datetime.strptime(time, '%H:%M:%S').time()
		# Inserting the invoice
		p = Invoice(email=request.user,from_date=verify.from_date,to_date=verify.to_date,year=verify.year,cost=cost,type="MONTHLY PAYMENT",status="GENERATE", date_audit=today_date_audit, hour_audit=time_audit)
		p.save(force_insert=True)
	else:
		today_date_object = datetime.strptime(request.session['value'], '%Y-%m-%d').date()
		currentYear = int(datetime.now().year)
		verify_month = Invoice.objects.filter(email=request.user, from_date__lte=today_date_object, to_date__gte=today_date_object, type="MONTHLY PAYMENT", year=currentYear)
		if verify_month.exists():
			# ONLY CHECKS IF THE USER CHANGED THE enrollment
			# FROM WORKOUT ONLY TO ALL CLASSES
			user = UserProfileInfo.objects.get(email=request.user)
			if user.active == 'ALL CLASSES':
				update_invoice = Invoice.objects.get(email=request.user, from_date__lte=today_date_object, to_date__gte=today_date_object, type="MONTHLY PAYMENT", year=currentYear)
				update_invoice.cost = 50
				update_invoice.save()
		else:
			flag_found = True
			dates = Invoice.objects.get(email=request.user, type="ENROLMENT FEE")
			year = dates.year
			to_date_invoice = dates.to_date
			while flag_found:
				#GETS THE ENROLLMENT DATE AS A PARAMETER TO MAKE THE COUNTING FOR FINDING OUT THE NEW MONTH
				from_1day = str(to_date_invoice + timedelta(days = 1))
				from_sameday = datetime.strptime(from_1day, '%Y-%m-%d').date()
				to_30days = str(from_sameday + timedelta(days = 30))
				to_30d_date = datetime.strptime(to_30days, '%Y-%m-%d').date()
				date_booked = datetime.strptime(request.session['value'], '%Y-%m-%d').date()
				if date_booked >= from_sameday and date_booked <= to_30d_date:
					user = UserProfileInfo.objects.get(email=request.user)
					cost = 35
					if user.active == 'WORKOUT ONLY':
						cost = 35
					else:
						cost = 50
					today_date = datetime.today().strftime('%Y-%m-%d')
					today_date_audit = datetime.strptime(today_date, '%Y-%m-%d').date()
					time = datetime.today().strftime('%H:%M:%S')
					time_audit = datetime.strptime(time, '%H:%M:%S').time()
					# Inserting the invoice
					p = Invoice(email=request.user,from_date=from_sameday,to_date=to_30d_date,year=year,cost=cost,type="MONTHLY PAYMENT",status="GENERATE", date_audit=today_date_audit, hour_audit=time_audit)
					p.save(force_insert=True)
					flag_found = False
				else:
					to_date_invoice = to_30d_date

# Check the jump slots and book the class
@login_required
def Check_Booking_jump(request, session):
    cancel = Jump.objects.filter(email_user=request.user, date=request.session['value'], session_number=session)
	# Checking if the user cancelled the slot and delete from the table
    if cancel.exists():
        cancel.delete()
        cancelling_allclases(request)
        context = {'response': 'Your booking have been successfully cancelled'}
        return render(request, 'ccfit_app/confirmation.html', context)
    else:
        flag_found = False
        models = [Workout, Pilates, Spin, Yoga, Jump]
		# checking all the tables
        for model in models:
            found_booking = model.objects.filter(email_user=request.user, date=request.session['value'])
            if found_booking.exists():
                flag_found = True
        if not flag_found:
            for n in range(1,7):
				# checking in all the sections
                if session == str(n):
                    today_date = datetime.today().strftime('%Y-%m-%d')
                    today_date_audit = datetime.strptime(today_date, '%Y-%m-%d').date()
                    time = datetime.today().strftime('%H:%M:%S')
                    time_audit = datetime.strptime(time, '%H:%M:%S').time()
                    booking = Jump(date=request.session['value'], email_user=request.user, session_number=session, date_audit=today_date_audit, hour_audit=time_audit)
                    #SEND EMAIL FUNCTIONALITY
                    context = {'session_1': {'start':'06:00', 'finish':'08:00', 'session_number': 1, 'expired':True,'status':'BOOK', 'enable':False},
                            'session_2': { 'start':'09:00', 'finish':'11:00', 'session_number': 2,  'expired':True, 'status':'BOOK', 'enable':False},
                            'session_3': { 'start':'12:00', 'finish':'14:00', 'session_number': 3,  'expired':True, 'status':'BOOK', 'enable':False},
                            'session_4': { 'start':'15:00', 'finish':'17:00', 'session_number': 4,  'expired':True, 'status':'BOOK', 'enable':False},
                            'session_5': { 'start':'18:00', 'finish':'20:00', 'session_number': 5,  'expired':True, 'status':'BOOK', 'enable':False},
                            'session_6': { 'start':'21:00', 'finish':'23:00', 'session_number': 6,  'expired':True, 'status':'BOOK', 'enable':False}}
                    invoice_insertion(request)
                    for key in context:
                        if session == str(context[key]['session_number']):
                            start = context[key]['start']
                            finish = context[key]['finish']
                            email_user = str(request.user)
                            message = 'Dear ' + str(request.user) + '\nThank you for booking the JUMP session with CCFIT. \nYour booking is now confirmed for: ' + str(request.session['value']) + ' \nStart Time '+ start + ' - ' + 'End Time ' + finish
                            send_mail('CCFIT Jump CLASS - Booking Confirmation', message, 'ccfitgym@gmail.com', [email_user], fail_silently=False)
            context = {'response': 'Your booking have been successfully confirmed'}
            booking.save()
        else:
            context = {'response': 'There is a class or workout session alredy booked for this date'}
        return render(request, 'ccfit_app/confirmation.html', context)


# Check the spin slots and book the class
@login_required
def Check_Booking_spin(request, session):
    cancel = Spin.objects.filter(email_user=request.user, date=request.session['value'], session_number=session)
	# Checking if the user cancelled the slot and delete from the table
    if cancel.exists():
        cancel.delete()
        cancelling_allclases(request)
        context = {'response': 'Your booking have been successfully cancelled'}
        return render(request, 'ccfit_app/confirmation.html', context)
    else:
        flag_found = False
        models = [Workout, Pilates, Spin, Yoga, Jump]
		# checking all the tables
        for model in models:
            found_booking = model.objects.filter(email_user=request.user, date=request.session['value'])
            if found_booking.exists():
                flag_found = True
        if not flag_found:
            for n in range(1,7):
				# checking in all the sections
                if session == str(n):
                    today_date = datetime.today().strftime('%Y-%m-%d')
                    today_date_audit = datetime.strptime(today_date, '%Y-%m-%d').date()
                    time = datetime.today().strftime('%H:%M:%S')
                    time_audit = datetime.strptime(time, '%H:%M:%S').time()
                    booking = Spin(date=request.session['value'], email_user=request.user, session_number=session, date_audit=today_date_audit, hour_audit=time_audit)
                    context = {'session_1': {'start':'06:00', 'finish':'08:00', 'session_number': 1, 'expired':True,'status':'BOOK', 'enable':False},
                            'session_2': { 'start':'09:00', 'finish':'11:00', 'session_number': 2,  'expired':True, 'status':'BOOK', 'enable':False},
                            'session_3': { 'start':'12:00', 'finish':'14:00', 'session_number': 3,  'expired':True, 'status':'BOOK', 'enable':False},
                            'session_4': { 'start':'15:00', 'finish':'17:00', 'session_number': 4,  'expired':True, 'status':'BOOK', 'enable':False},
                            'session_5': { 'start':'18:00', 'finish':'20:00', 'session_number': 5,  'expired':True, 'status':'BOOK', 'enable':False},
                            'session_6': { 'start':'21:00', 'finish':'23:00', 'session_number': 6,  'expired':True, 'status':'BOOK', 'enable':False}}
                    invoice_insertion(request)
                    for key in context:
                        if session == str(context[key]['session_number']):
                            start = context[key]['start']
                            finish = context[key]['finish']
                            email_user = str(request.user)
                            message = 'Dear ' + str(request.user) + '\nThank you for booking the Spin session with CCFIT. \nYour booking is now confirmed for: ' + str(request.session['value']) + ' \nStart Time '+ start + ' - ' + 'End Time ' + finish
                            send_mail('CCFIT Spin CLASS - Booking Confirmation', message, 'ccfitgym@gmail.com', [email_user], fail_silently=False)
            context = {'response': 'Your booking have been successfully confirmed'}
            booking.save()
        else:
            context = {'response': 'There is a class or workout session alredy booked for this date'}
        return render(request, 'ccfit_app/confirmation.html', context)


# Check the yoga slots and book the class
@login_required
def Check_Booking_yoga(request, session):
    cancel = Yoga.objects.filter(email_user=request.user, date=request.session['value'], session_number=session)
	# Checking if the user cancelled the slot and delete from the table
    if cancel.exists():
        cancel.delete()
        cancelling_allclases(request)
        context = {'response': 'Your booking have been successfully cancelled'}
        return render(request, 'ccfit_app/confirmation.html', context)
    else:
        flag_found = False
        models = [Workout, Pilates, Spin, Yoga, Jump]
		# checking all the tables
        for model in models:
            found_booking = model.objects.filter(email_user=request.user, date=request.session['value'])
            if found_booking.exists():
                flag_found = True
        if not flag_found:
            for n in range(1,7):
				# checking in all the sections
                if session == str(n):
                    today_date = datetime.today().strftime('%Y-%m-%d')
                    today_date_audit = datetime.strptime(today_date, '%Y-%m-%d').date()
                    time = datetime.today().strftime('%H:%M:%S')
                    time_audit = datetime.strptime(time, '%H:%M:%S').time()
                    booking = Yoga(date=request.session['value'], email_user=request.user, session_number=session, date_audit=today_date_audit, hour_audit=time_audit)
                    context = {'session_1': {'start':'06:00', 'finish':'08:00', 'session_number': 1, 'expired':True,'status':'BOOK', 'enable':False},
                            'session_2': { 'start':'09:00', 'finish':'11:00', 'session_number': 2,  'expired':True, 'status':'BOOK', 'enable':False},
                            'session_3': { 'start':'12:00', 'finish':'14:00', 'session_number': 3,  'expired':True, 'status':'BOOK', 'enable':False},
                            'session_4': { 'start':'15:00', 'finish':'17:00', 'session_number': 4,  'expired':True, 'status':'BOOK', 'enable':False},
                            'session_5': { 'start':'18:00', 'finish':'20:00', 'session_number': 5,  'expired':True, 'status':'BOOK', 'enable':False},
                            'session_6': { 'start':'21:00', 'finish':'23:00', 'session_number': 6,  'expired':True, 'status':'BOOK', 'enable':False}}

                    invoice_insertion(request)
                    for key in context:
                        if session == str(context[key]['session_number']):
                            start = context[key]['start']
                            finish = context[key]['finish']
                            email_user = str(request.user)
                            message = 'Dear ' + str(request.user) + '\nThank you for booking the Yoga session with CCFIT. \nYour booking is now confirmed for: ' + str(request.session['value']) + ' \nStart Time '+ start + ' - ' + 'End Time ' + finish
                            send_mail('CCFIT Yoga CLASS - Booking Confirmation', message, 'ccfitgym@gmail.com', [email_user], fail_silently=False)
            context = {'response': 'Your booking have been successfully confirmed'}
            booking.save()
        else:
            context = {'response': 'There is a class or workout session alredy booked for this date'}
        return render(request, 'ccfit_app/confirmation.html', context)


# Check the pilates slots and book the class
@login_required
def Check_Booking_pilates(request, session):
    cancel = Pilates.objects.filter(email_user=request.user, date=request.session['value'], session_number=session)
	# Checking if the user cancelled the slot and delete from the table
    if cancel.exists():
        cancel.delete()
        cancelling_allclases(request)
        context = {'response': 'Your booking have been successfully cancelled'}
        return render(request, 'ccfit_app/confirmation.html', context)
    else:
        flag_found = False
        models = [Workout, Pilates, Spin, Yoga, Jump]
		# checking all the tables
        for model in models:
            found_booking = model.objects.filter(email_user=request.user, date=request.session['value'])
            if found_booking.exists():
                flag_found = True
        if not flag_found:
            for n in range(1,7):
				# checking in all the sections
                if session == str(n):
                    today_date = datetime.today().strftime('%Y-%m-%d')
                    today_date_audit = datetime.strptime(today_date, '%Y-%m-%d').date()
                    time = datetime.today().strftime('%H:%M:%S')
                    time_audit = datetime.strptime(time, '%H:%M:%S').time()
                    booking = Pilates(date=request.session['value'], email_user=request.user, session_number=session, date_audit=today_date_audit, hour_audit=time_audit)
                    context = {'session_1': {'start':'06:00', 'finish':'08:00', 'session_number': 1, 'expired':True,'status':'BOOK', 'enable':False},
                            'session_2': { 'start':'09:00', 'finish':'11:00', 'session_number': 2,  'expired':True, 'status':'BOOK', 'enable':False},
                            'session_3': { 'start':'12:00', 'finish':'14:00', 'session_number': 3,  'expired':True, 'status':'BOOK', 'enable':False},
                            'session_4': { 'start':'15:00', 'finish':'17:00', 'session_number': 4,  'expired':True, 'status':'BOOK', 'enable':False},
                            'session_5': { 'start':'18:00', 'finish':'20:00', 'session_number': 5,  'expired':True, 'status':'BOOK', 'enable':False},
                            'session_6': { 'start':'21:00', 'finish':'23:00', 'session_number': 6,  'expired':True, 'status':'BOOK', 'enable':False}}
                    invoice_insertion(request)
                    for key in context:
                        if session == str(context[key]['session_number']):
                            start = context[key]['start']
                            finish = context[key]['finish']
                            email_user = str(request.user)
                            message = 'Dear ' + str(request.user) + '\nThank you for booking the Pilates session with CCFIT. \nYour booking is now confirmed for: ' + str(request.session['value']) + ' \nStart Time '+ start + ' - ' + 'End Time ' + finish
                            send_mail('CCFIT Pilates CLASS - Booking Confirmation', message, 'ccfitgym@gmail.com', [email_user], fail_silently=False)
            context = {'response': 'Your booking have been successfully confirmed'}
            booking.save()
        else:
            context = {'response': 'There is a class or workout session alredy booked for this date'}
        return render(request, 'ccfit_app/confirmation.html', context)



# Check the jump workout and book the class
@login_required
def Check_Booking_workout(request, session):
    cancel = Workout.objects.filter(email_user=request.user, date=request.session['value'], session_number=session)
	# Checking if the user cancelled the slot and delete from the table
    if cancel.exists():
        cancel.delete()
		# VERIFICAR TODOS OS BOOKINGS
        user = UserProfileInfo.objects.get(email=request.user)
        if user.active == 'WORKOUT ONLY':
	        program_date = datetime.strptime(request.session['value'], '%Y-%m-%d').date()
	        invoice = Invoice.objects.get(email=request.user, from_date__lte=program_date, to_date__gte=program_date, type="MONTHLY PAYMENT")
	        number_bookings = Workout.objects.filter(email_user=request.user, date__gte=invoice.from_date)
	        if number_bookings.exists():
	            number_bookings = Workout.objects.filter(email_user=request.user, date__lte=invoice.to_date)
	            if not number_bookings.exists():
	                invoice.delete()
	        else:
				# deleting invoice
	            invoice.delete()
        else:
            cancelling_allclases(request)
        context = {'response': 'Your booking have been successfully cancelled'}
        return render(request, 'ccfit_app/confirmation.html', context)
    else:
        flag_found = False
        models = [Workout, Pilates, Spin, Yoga, Jump]
		# checking all the tables
        for model in models:
            found_booking = model.objects.filter(email_user=request.user, date=request.session['value'])
            if found_booking.exists():
                flag_found = True
        if not flag_found:
            for n in range(1,7):
				# checking in all the sections
                if session == str(n):
                    today_date = datetime.today().strftime('%Y-%m-%d')
                    today_date_audit = datetime.strptime(today_date, '%Y-%m-%d').date()
                    time = datetime.today().strftime('%H:%M:%S')
                    time_audit = datetime.strptime(time, '%H:%M:%S').time()
                    booking = Workout(date=request.session['value'], email_user=request.user, session_number=session, date_audit=today_date_audit, hour_audit=time_audit)
                    context = {'session_1': {'start':'06:00', 'finish':'08:00', 'session_number': 1, 'expired':True,'status':'BOOK', 'enable':False},
                            'session_2': { 'start':'09:00', 'finish':'11:00', 'session_number': 2,  'expired':True, 'status':'BOOK', 'enable':False},
                            'session_3': { 'start':'12:00', 'finish':'14:00', 'session_number': 3,  'expired':True, 'status':'BOOK', 'enable':False},
                            'session_4': { 'start':'15:00', 'finish':'17:00', 'session_number': 4,  'expired':True, 'status':'BOOK', 'enable':False},
                            'session_5': { 'start':'18:00', 'finish':'20:00', 'session_number': 5,  'expired':True, 'status':'BOOK', 'enable':False},
                            'session_6': { 'start':'21:00', 'finish':'23:00', 'session_number': 6,  'expired':True, 'status':'BOOK', 'enable':False}}
                    invoice_insertion(request)
					# check first if there is no invoice
                    for key in context:
                        if session == str(context[key]['session_number']):
                            start = context[key]['start']
                            finish = context[key]['finish']
                            email_user = str(request.user)
                            message = 'Dear ' + str(request.user) + '\nThank you for booking the Workout session with CCFIT. \nYour booking is now confirmed for: ' + str(request.session['value']) + ' \nStart Time '+ start + ' - ' + 'End Time ' + finish
                            send_mail('CCFIT Workout CLASS - Booking Confirmation', message, 'ccfitgym@gmail.com', [email_user], fail_silently=False)
            context = {'response': 'Your booking have been successfully confirmed'}
            booking.save()
        else:
            context = {'response': 'There is a class or workout session alredy booked for this date'}
        return render(request, 'ccfit_app/confirmation.html', context)

# Bookingpage for selecting the section
@login_required
def BookingPage(request):
	request.session['confirm_message'] = ''
	form = ExampleForm()
	return render(request, 'ccfit_app/booking_page.html', {'form':form})

# Function that redirects to the check_classes page
@login_required
@admin_teacher_only
def CheckingPage(request):
    form = ExampleForm()
    return render(request, 'ccfit_app/check_classes.html', {'form':form})


# Class to create the profile user info
class CreateProfilePageView(LoginRequiredMixin, CreateView):
    model = UserProfileInfo
    form_class = ProfilePageForm
    template_name = "ccfit_app/create_user_profile_page.html"

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

# Class to update the profile user info
class EditProfilePageView(LoginRequiredMixin, generic.UpdateView):
    model = UserProfileInfo
    template_name = "ccfit_app/edit_profile_page.html"
    form_class = ProfilePageForm
    success_url = reverse_lazy('ccfit:index')

	# Runs as soon as the page is opened
	# Runs as soon as the page is opened
    def get(self, request, pk):
        request.session['confirm_message'] = ''
        obj = get_object_or_404(UserProfileInfo, pk = pk)
        form = ProfilePageForm(instance = obj)
        return render(request, 'ccfit_app/edit_profile_page.html', {'form': form, 'type_user': obj.type})

	# Runs when the submit is pressed
    def post(self, request, pk):
        obj = get_object_or_404(UserProfileInfo, pk = pk)
        form = ProfilePageForm(data=request.POST, instance = obj)
        if  form.is_valid():
            profile = form.save(commit=False)
            profile.registration_completed = True
            profile.active = profile.membership
			# Validates the date and hour so the user can use it as
			# audit info
            user = UserProfileInfo.objects.get(email=request.user)
            if user.type == 'USER':
	            today_date = datetime.today().strftime('%Y-%m-%d')
	            today_date_object = datetime.strptime(today_date, '%Y-%m-%d').date()
	            currentYear = int(datetime.now().year)
	            verify_enrollment = Invoice.objects.filter(email=profile.email, type='ENROLMENT FEE')
	            future_30days=str(today_date_object + timedelta(days = 30))
	            future_30days = datetime.strptime(future_30days, '%Y-%m-%d').date()
	            if not verify_enrollment.exists():
	                today_date = datetime.today().strftime('%Y-%m-%d')
	                today_date_audit = datetime.strptime(today_date, '%Y-%m-%d').date()
	                time = datetime.today().strftime('%H:%M:%S')
	                time_audit = datetime.strptime(time, '%H:%M:%S').time()
					# Inserting the data retrieved to the invoice table creating the
					# first invoice 'ENROLLMENT FEE' as soon as the user creates the profile
	                p = Invoice(email=profile.email,
		            			 from_date=today_date_object,
								 to_date=future_30days,
		            			 year=currentYear,
		            			 cost=30,
		            			 type="ENROLMENT FEE",
		            			 status="GENERATE",
								 date_audit=today_date_audit,
								 hour_audit=time_audit)
	                p.save(force_insert=True)
            profile.save()
            return HttpResponseRedirect(reverse_lazy('ccfit:index'))
        else:
            return HttpResponseRedirect(reverse_lazy('ccfit:index'))

# View to change the password
class PasswordsChangeView(LoginRequiredMixin, PasswordChangeView):
    form_class = PasswordChangeForm
    template_name = "ccfit_app/change_password.html"
    success_url = reverse_lazy('ccfit:password_sucess')

# View of confirmation
@login_required
def password_sucess(request):
    return render(request, 'ccfit_app/password_sucess.html', {})


def LoginView(request):
	request.session['confirm_message'] = ''
	print('GOT HERE IN THE LOGINVIEW')
	if request.method == 'POST':
		print(request.POST.get('email'))
		print(request.POST.get('password'))
		email = request.POST.get('email')
		password = request.POST.get('password')
		# Authenticating the user
		user = authenticate(request, email=email, password=password)
		print(user)
		if user is not None:
			login(request, user)
			return HttpResponseRedirect(reverse_lazy('ccfit:index'))
		else:
			return HttpResponseRedirect(reverse_lazy('ccfit:index'))
	context = {}
	return render(request, 'ccfit_app/login.html', context)

# Sign up form
def create_user(request):
    if request.method=='POST':
        form = UserCreateForm(data=request.POST)
        profile_form = UserProfileInfoForm(data=request.POST)
		# This whole code block is to do with the insertion of UserProfileInfo
		# info to the form and the table subsequently
        if form.is_valid() and profile_form.is_valid():
            user = form.save()
            user.save()
            profile = profile_form.save(commit=False)
            profile.email = user.email
            profile.user = user
            today_date = datetime.today().strftime('%Y-%m-%d')
            today_date_audit = datetime.strptime(today_date, '%Y-%m-%d').date()
            time = datetime.today().strftime('%H:%M:%S')
            time_audit = datetime.strptime(time, '%H:%M:%S').time()
            profile.date_audit = today_date_audit
            profile.hour_audit = time_audit
            profile.save()
            email = request.POST['email']
            password = request.POST['password1']
			# Authenticating the user
            user = authenticate(email=form.cleaned_data['email'], password=form.cleaned_data['password1'])
			# login the user
            login(request, user)
            return HttpResponseRedirect(reverse_lazy('ccfit:index'))
    else:
        form = UserCreateForm()
        profile_form = UserProfileInfoForm()

    context = {'form': form, 'profile_form': profile_form}
    return render(request, 'ccfit_app/signup.html', context)



# Edit profile
class EditProfile(LoginRequiredMixin, generic.UpdateView):

    form_class = forms.EditProfileForm
    success_url = reverse_lazy('ccfit:index')
    template_name = "ccfit_app/edit_profile.html"

    def get_object(self):
        self.request.session['confirm_message'] = ''
        print('CHEEEECK IFSS GOTTEN EHEHHHHHHHHHHHERE')
        return self.request.user


# Index view that retrieves the user info for
# permissions on the index page
@login_required
def index(request):
	#user info
    user = UserProfileInfo.objects.filter(email=request.user)
    value_type = 'USER'
    registered = False
    status = 'PAID'
    status_mp = 'GENERATE'
	# checking the user info
    if user.exists():
        for course in user:
            value_type = course.type
            registered = course.registration_completed
            nickname = course.nickname
	#invoice info for enrollment fee
    verify_enrollment = Invoice.objects.filter(email=request.user, type='ENROLMENT FEE')
    if verify_enrollment.exists():
        for course in verify_enrollment:
            status = course.status

	#invoice info for enrollment fee
    verify_enrollment_MP = Invoice.objects.filter(email=request.user, type='MONTHLY PAYMENT')
    if verify_enrollment_MP.exists():
        for course in verify_enrollment_MP:
            status_mp = course.status
            if status_mp == 'REQUESTED':
                break
    print(registered)
    print('registeressssssssssssssssssssssssssssssssssssssssssd')
    mydict = {'type': value_type, 'registration': registered, 'status': status, 'status_MP': status_mp, 'nickname': nickname}
    return render(request, 'ccfit_app/index.html', mydict)


# User's list to query on it
@method_decorator(admin_only, name='dispatch')
class UsersListView(LoginRequiredMixin, ListView):
    template_name = "ccfit_app/allUsers.html"
    model = UserProfileInfo
    context_object_name = "users"

    def get_queryset(self):
        email = self.request.GET.get('search')
        object_list = self.model.objects.all()
        if email:
            object_list = object_list.filter(email__contains=email)
        return object_list

# Class to update the users on the manage users page
@method_decorator(admin_only, name='dispatch')
class UsersUpdateView(LoginRequiredMixin, UpdateView):
    model = UserProfileInfo
    template_name = "ccfit_app/updateUsers.html"
    form_class = UserProfileInfoFormUsers
    success_url = reverse_lazy('ccfit:all_users')

	# retrieves users when opens the page
    def get(self, request, pk):
        obj = get_object_or_404(UserProfileInfo, pk = pk)
        form = UserProfileInfoFormUsers(instance = obj)
        return render(request, 'ccfit_app/updateUsers.html', {
        'form': form, 'type_user': obj.type
    })

	# send info when the submit button is pressed
    def post(self, request, pk):
        obj = get_object_or_404(UserProfileInfo, pk = pk)
        form = UserProfileInfoFormUsers(data=request.POST, instance = obj)
        if  form.is_valid():
            system_user = User.objects.get(email=obj.email)
            type_user = obj.type
			# Checks if the user is ADMINISTRATOR and change the setup
			# is_superuser for the standart USER table
            if type_user == 'ADMINISTRATOR':
                system_user.is_superuser= True
                system_user.is_staff= True
            else:
                system_user.is_superuser= False
                system_user.is_staff= False
            system_user.save()
            profile = form.save(commit=False)
            profile.membership = profile.active
            profile.save()
            return HttpResponseRedirect(reverse_lazy('ccfit:all_users'))
        else:
            return HttpResponseRedirect(reverse_lazy('ccfit:all_users'))
