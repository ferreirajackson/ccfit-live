from django.shortcuts import render, redirect, get_object_or_404, redirect
from django.http import HttpResponse
from .models import Workout, UserProfileInfo, Pilates, Yoga, Spin, Jump, User, MaxSession, Invoice
from django.contrib.auth.decorators import login_required
from . import forms
from django.views import generic
from ccfit_app.forms import SignUpForm, EditProfileForm, ProfilePageForm, ExampleForm, UserProfileInfoForm, UserCreateForm, WorkoutForm, UserUpdateForm, UserProfileInfoFormUsers
from django.contrib.auth import login, logout, authenticate, login
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, PasswordChangeForm
from django.urls import reverse_lazy, reverse
from django.contrib.auth.views import PasswordChangeView
from django.views.generic import CreateView, UpdateView, TemplateView, ListView, View
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from datetime import datetime, timedelta
import time
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import send_mail
from .decorators import user_all_classes, user_workout, admin_only
from django.utils.decorators import method_decorator
from io import BytesIO
from django.template.loader import get_template
import stripe
from xhtml2pdf import pisa
import os

# Create your views here.
# stripe.api_key = os.environ.get('STRIPE_PRIVATE_KEY')
stripe.api_key = 'sk_test_51I8CofKwMtRnc3TERmC6RgEX2KX4okNeqmnHVAZwu0wCva0SewBG1x6BJ5yOpPik2qct0yNaewqrLNerI7oQbdLf00Oyz3Ulph'

@login_required
def Payment_request(request):
	print(request.session['type_payment'])
	print(type(request.session['type_payment']))
	if request.session['type_payment'] == '1':
		amount = 30
		description = 'enrollment fee'
	else:
		# ADICIONAR AQUI A OPÇÃO DE PAGAMENTO PARA WORKOUT ONLY = 35
		# pegar todas as infos daqui tbm
		# **************************************************************************************
		user = UserProfileInfo.objects.get(email=request.user)
		if user.active == 'ALL CLASSES':
			amount = 50
		elif user.active == 'WORKOUT ONLY':
			amount = 35
		else:
			print('It wasnt possible to finish the transaction')
		# **************************************************************************************

		description = 'monthly payment'

	print(amount)
	if request.method == 'POST':
		print('Data:', request.POST)



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

		#UPDATING STATUS E DATAS
		if request.session['type_payment'] == '1':
			verify_enrollment = Invoice.objects.get(email=request.user, type='ENROLLMENT FEE')
			# user = UserProfileInfo.objects.get(email=request.user)
			today_date = datetime.today().strftime('%Y-%m-%d')
			today_date_object = datetime.strptime(today_date, '%Y-%m-%d').date()
			future_30days = str(today_date_object + timedelta(days = 30))
			future_30days_DATE = datetime.strptime(future_30days, '%Y-%m-%d').date()
			print(future_30days_DATE, 'future_30days_DATE')
			verify_enrollment.from_date = today_date_object
			verify_enrollment.to_date = future_30days_DATE
			verify_enrollment.status = 'PAID'
			verify_enrollment.save()
			user = UserProfileInfo.objects.get(email=request.user)
			cost = 35
			if user.active == 'WORKOUT ONLY':
				cost = 35
			else:
				cost = 50
			p = Invoice(email=verify_enrollment.email,from_date=verify_enrollment.from_date,to_date=verify_enrollment.to_date,year=verify_enrollment.year,cost=cost,type="MONTHLY PAYMENT",status="GENERATE")
			p.save(force_insert=True)
		elif request.session['type_payment'] == '2':
			# verificar qual a chave certa para fazer essar busca e pegar apenas um registro
			verify_enrollment = Invoice.objects.filter(email=request.user, type='MONTHLY PAYMENT', status='REQUESTED').order_by('from_date')
			print(verify_enrollment)
			if verify_enrollment.exists():
				for course in verify_enrollment:
					verify_enrollment_unique = Invoice.objects.get(pk=course.pk)
					verify_enrollment_unique.status = 'PAID'
					verify_enrollment_unique.save()
					break
			# user = UserProfileInfo.objects.get(email=request.user)
			# verify_enrollment.status = 'PAID'
			# verify_enrollment.save()
		else:
			pass
	return HttpResponseRedirect(reverse_lazy('ccfit:index'))

@login_required
@method_decorator(admin_only, name='dispatch')
def MarkPaid(request, pk):
	print('testing')
	print('testing ', pk )
	verify_enrollment = Invoice.objects.get(pk=pk)
	verify_enrollment.status = 'PAID'
	verify_enrollment.save()
	return HttpResponseRedirect(reverse_lazy('ccfit:invoices'))


@login_required
@method_decorator(admin_only, name='dispatch')
def SendInvoice(request, pk):
	print('testing SEND INVOICE')
	print('testing ', pk )
	verify_enrollment = Invoice.objects.get(pk=pk)
	verify_enrollment.status = 'REQUESTED'
	verify_enrollment.save()
	email_user = str(verify_enrollment.email)
	print(email_user)
	message = 'Dear ' + str(verify_enrollment.email) + '\nThank you for trusting CCFIT to be your gym. \nYour invoice for this month is now availabe.' + ' \nCheck on https://ccfitgym.herokuapp.com/ to pay'
	send_mail('CCFIT Invoice: ' + str(verify_enrollment.from_date) + ' - ' + str(verify_enrollment.to_date), message, 'ccfitgym@gmail.com', [email_user], fail_silently=False)
	return HttpResponseRedirect(reverse_lazy('ccfit:invoices'))

@login_required
def Payment(request, type):
    request.session['type_payment'] = type
    print(request.session['type_payment'])
    return render(request, 'ccfit_app/payment.html')


@method_decorator(admin_only, name='dispatch')
class InvoiceListView(LoginRequiredMixin, ListView):
	print('TESTING')
	template_name = "ccfit_app/invoices.html"
	model = Invoice
	context_object_name = "invoices"



def render_to_pdf(template_src, context_dict={}):
	template = get_template(template_src)
	html  = template.render(context_dict)
	result = BytesIO()
	pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
	if not pdf.err:
		return HttpResponse(result.getvalue(), content_type='application/pdf')
	return None


#Opens up page as PDF
@method_decorator(admin_only, name='dispatch')
class ViewPDF(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        data = {
            "company": "Display",
        	"address": "123 Street name",
        	"city": "Vancouver",
        	"state": "WA",
        	"zipcode": "98663",
            "phone": "555-555-2345",
        	"email": "youremail@dennisivy.com",
        	"website": "dennisivy.com",
        }
        pdf = render_to_pdf('ccfit_app/pdf_template.html', data)

        return HttpResponse(pdf, content_type='application/pdf')


class InvoiceUser(LoginRequiredMixin, View):
	def get(self, request, *args, **kwargs):
		print('firts thing print pk')
		#print(pk)
		self.kwargs['pk']
		print(self.kwargs['pk'])
		new = Invoice.objects.filter(pk=self.kwargs['pk'])
		if new.exists():
			for unit in new:
				print(unit.email, 'this')
				print(unit.from_date, 'this')
				print(unit.to_date, 'this')
				print(unit.year, 'this')
				print(unit.cost, 'this')
				print(unit.type, 'this')
				print(unit.status, 'this')

				d1 = {'email': unit.email, 'from_date': str(unit.from_date), 'to_date': str(unit.to_date), 'cost': unit.cost, 'type': unit.type}
		else:
			print("DIDNT FIND", num)
		print('HERE I WANT TO SEE THE RESULT OF THE DICT AND LIST')
		print(d1)
		print('**********************************************************************************')
		pdf = render_to_pdf('ccfit_app/invoice_template.html', d1)

		return HttpResponse(pdf, content_type='application/pdf')


class PDF(LoginRequiredMixin, View):
	def get(self, request, *args, **kwargs):
		print(request.session['value'])
		dict = {'1': Workout,'2': Pilates,'3': Jump,'4': Spin,'5': Yoga}
		class_number = str(request.session['class'])
		print(dict[class_number])
		print(type(dict[class_number]))
		list = [1,2,3,4,5]
		list_user = []
		data_second = {}
		for num in list:
			new = dict[class_number].objects.filter(date=request.session['value'], session_number=num)
			if new.exists():
				for unit in new:
					print(unit.date, 'this')
					print(unit.email_user, 'this')
					print(unit.session_number, 'this')
					list_user.append(unit.email_user)
				d1 = {str(num): list_user}
				data_second.update(d1)
				list_user = []
			else:
				print("NOTHING FOR THIS ", num)
		print('HERE I WANT TO SEE THE RESULT OF THE DICT AND LIST')
		print(data_second)
		print('**********************************************************************************')
		context = {"work" : Workout.objects.filter(date=self.request.session['value']).order_by('session_number')}
		data = {
		"company": "Display",
		"address": "123 Street name",
		"city": "Vancouver",
		"state": "WA",
		"zipcode": "98663",
		"phone": "555-555-2345",
		"email": "youremail@dennisivy.com",
		"website": "dennisivy.com",

		}
		pdf = render_to_pdf('ccfit_app/pdf_template.html', {'data': data_second})

		return HttpResponse(pdf, content_type='application/pdf')



#Automaticly downloads to PDF file
class DownloadPDF(LoginRequiredMixin, View):
	def get(self, request, *args, **kwargs):
		print(request.session['value'])
		dict = {'1': Workout,'2': Pilates,'3': Jump,'4': Spin,'5': Yoga}
		class_number = str(request.session['class'])
		print(dict[class_number])
		print(type(dict[class_number]))
		list = [1,2,3,4,5]
		list_user = []
		data_second = {}
		for num in list:
			new = dict[class_number].objects.filter(date=request.session['value'], session_number=num)
			if new.exists():
				for unit in new:
					print(unit.date, 'this')
					print(unit.email_user, 'this')
					print(unit.session_number, 'this')
					list_user.append(unit.email_user)
				d1 = {str(num): list_user}
				data_second.update(d1)
				list_user = []
			else:
				print("NOTHING FOR THIS ", num)
		print('HERE I WANT TO SEE THE RESULT OF THE DICT AND LIST')
		print(data_second)
		print('**********************************************************************************')
		context = {"work" : Workout.objects.filter(date=self.request.session['value']).order_by('session_number')}

		pdf = render_to_pdf('ccfit_app/pdf_template.html', {'data': data_second})
		response = HttpResponse(pdf, content_type='application/pdf')
		content = 'attachment; filename="report.pdf"'
		response['Content-Disposition'] = content
		return response


@login_required
def Confirmation_Booking(request, n1):
    return render(request, 'ccfit_app/confirmation.html', context)


@login_required
def MyBookings(request):
    models = [Workout, Pilates, Spin, Yoga, Jump]
    data = {}
    new = {}
    sessions = {'1': 'from 06:00 to 08:00','2': 'from 09:00 to 11:00','3': 'from 12:00 to 14:00','4': 'from 15:00 to 17:00','5': 'from 18:00 to 20:00', '6': 'from 21:00 to 23:00'}
    for model in models:
        found_booking = model.objects.filter(email_user=request.user)
        print('THE FIRST MODEL IS : ', model)
        if found_booking.exists():
            print('WE FOUND BOOKINGSSSSSSSSSSSSSSSSSSS')
            for unit in found_booking:
                print(unit.date, 'unit')
                print(unit.email_user, 'unit')
                print(unit.session_number, 'unit')
                print()
                d1 = {str(unit.date): [str(request.user), sessions[str(unit.session_number)], model.__name__]}
                data.update(d1)

    print(data)
    print('THIS IS THE DATA DICT')
    for key in sorted(data):
        print("%s: %s" % (key, data[key]))
        new[key] = data[key]
    print('PRINTING OUTSIDE')
    print(new)
    #data = {'today':  ['jackson', 'session_1', 'Pilates'] , 'tomorrow':  ['jackson', 'session_2', 'Jump'] ,'day_after':  ['jackson', 'session_46', 'workout']}
    return render(request, 'ccfit_app/my_bookings.html', {'data': new})


@login_required
@admin_only
def Validate_date_check(request):
    print('IT GOT HEREEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE')
    if request.is_ajax():
        global date
        date  = request.POST.get('date_verification')
        request.session['value'] = date
        print(date)
        print('print this')
        name_dict = \
                            {
                                'workout': 'false',
                                'pilates': 'false',
                                'spin': 'false',
                                'jump': 'false',
                                'yoga': 'false',
                             }
            #print('PRINTING THE NAMEDICT:  ', name_dict)
        return JsonResponse(name_dict)
    return render(request, 'ccfit_app/check_classes.html')


@login_required
def Validate_date(request):
    print('IT GOT HEREEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE')
    if request.is_ajax():
        global date
        date  = request.POST.get('date_verification')
        request.session['value'] = date
        print(date)
        print('print this')
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


@login_required
def Check_Class_Amount(request, session):
    cancel = User.objects.filter(email=request.user)
    print('CHECKING am')
    if cancel.exists():
        context = {}
        list = []
        class_name = request.session['class']
        dict = {'1': Workout,'2': Pilates,'3': Jump,'4': Spin,'5': Yoga}
        print(dict[class_name])
        new = dict[class_name].objects.filter(date=request.session['value'], session_number=session)
        print(new, 'THIS IS CANCELLLLLLLLL')
        if new.exists():
            for unit in new:
                print(unit.email_user, 'unit')
                list.append(unit.email_user)

        context['emails'] = list
        print(context, 'THIS IS THE MAIN DICT')
        return render(request, 'ccfit_app/class_amount.html', context)



@login_required
@admin_only
def ClassesCountView(request, class_number):
    cancel = User.objects.filter(email=request.user)
    print('CHECKING')
    if cancel.exists():
        print('it has to print something here')
        print('AND PRINTED THE CLASS', class_number)
        dict = {'1': Workout,'2': Pilates,'3': Jump,'4': Spin,'5': Yoga}
        list = [1,2,3,4,5]
        #print(dict[class_number])
        #print(type(dict[class_number]))
        #request.session['class_name_session'] = dict[class_number]
        #print(request.session['class_name_session'])
        #getting the value of the class
        request.session['class'] = class_number


        context = {'session_1': {'start':'06:00', 'finish':'08:00', 'session_number': 1, '1': 0, 'enable':False},
                'session_2': { 'start':'09:00', 'finish':'11:00', 'session_number': 2, '2': 0, 'enable':False},
                'session_3': { 'start':'12:00', 'finish':'14:00', 'session_number': 3, '3': 0, 'enable':False},
                'session_4': { 'start':'15:00', 'finish':'17:00', 'session_number': 4, '4': 0, 'enable':False},
                'session_5': { 'start':'18:00', 'finish':'20:00', 'session_number': 5, '5': 0, 'enable':False},
                'session_6': { 'start':'21:00', 'finish':'23:00', 'session_number': 6, '6': 0, 'enable':False}}
        #print(dict[class_number], 'this is supposed to be the number')
        #new_dict = {'1': 0,'2': 0,'3': 0,'4': 0,'5': 0,'6': 0}
        found_booking = dict[class_number].objects.filter(date=request.session['value']).values('session_number')
        print(found_booking)
        if found_booking.exists():
            for unit in found_booking:
                session_number_keep = unit['session_number']
                print(session_number_keep)
                session_number_keep = str(session_number_keep)
                print(type(session_number_keep))
                session_id = 'session_' + session_number_keep
                context[session_id][session_number_keep] += 1
                if context[session_id]['enable'] == False:
                    context[session_id]['enable'] = True
                    print('UPDATED')
                print(context, 'lets see')
    #found_booking = model.objects.filter(email_user=request.user, date=request.session['value'])


    return render(request, 'ccfit_app/count_classes.html', context)


@method_decorator(user_workout, name='dispatch')
class WorkoutView(LoginRequiredMixin, generic.TemplateView):
    model = Workout
    template_name = "ccfit_app/workout.html"

    def get_context_data(self, **kwargs):
        context = super(WorkoutView, self).get_context_data(**kwargs)
        print('DO THE TIME SCHEME HERE')
        booked_flag = 'N'

        if 'value' in self.request.session:
            booking_date = self.request.session['value']
            print(booking_date)

            #BOOKING DATE
            booking_date_object = datetime.strptime(booking_date, '%Y-%m-%d').date()
            #print(type(booking_date_object))
            #print(booking_date_object)  # printed in default formatting

            #TODAY'S DATE
            today_date = datetime.today().strftime('%Y-%m-%d')
            today_date_object = datetime.strptime(today_date, '%Y-%m-%d').date()
            #print(type(today_date_object))
            context = {'session_1': {'start':'06:00', 'finish':'08:00', 'session_number': 1, 'expired':True,'status':'BOOK', 'enable':False},
                    'session_2': { 'start':'09:00', 'finish':'11:00', 'session_number': 2,  'expired':True, 'status':'BOOK', 'enable':False},
                    'session_3': { 'start':'12:00', 'finish':'14:00', 'session_number': 3,  'expired':True, 'status':'BOOK', 'enable':False},
                    'session_4': { 'start':'15:00', 'finish':'17:00', 'session_number': 4,  'expired':True, 'status':'BOOK', 'enable':False},
                    'session_5': { 'start':'18:00', 'finish':'20:00', 'session_number': 5,  'expired':True, 'status':'BOOK', 'enable':False},
                    'session_6': { 'start':'21:00', 'finish':'23:00', 'session_number': 6,  'expired':True, 'status':'BOOK', 'enable':False}}

            # IF HERE TO CHECK IF THERE IS ALREADY A BOOKING FOR THIS DAY
            print(self.request.user)
            print(self.request.session['value'])
            user = Workout.objects.filter(email_user=self.request.user, date=self.request.session['value']).values('session_number')
            print('TOOK THE VALUE HEREEEEEEEEEEEEEEEEEE')
            print('DID SOMETHING NEW HEREEEEEEEEEEEEEEEEEEFDDDDDDDDFDFSD')
            print(user)
            if user.exists():
                booked_flag = 'Y'
                for course in user:
                    session_number_keep = course['session_number']
                    print(session_number_keep)
            ###############################################################
            ###############################################################
            if booking_date_object == today_date_object:
                #do something
                print(time.strftime("%H:%M"))
                start_hour = time.strftime("%H")
                start_minute = time.strftime("%M")

                for key in context:
                    print(context[key]['start'])
                    schedule_date = context[key]['start']

                    start_time = (int(schedule_date[0:2])*60 + int(schedule_date[3:5])-30)
                    current_time =  datetime.now().hour*60 +datetime.now().minute
                    print(start_time, 'START TIME')
                    print(current_time , 'CURRENT TIME')
                    if start_time <= current_time:
                        context[key]['expired'] = False

                    #Getting the number max of users per session and class from table MaxSession model
                    num_max_users = MaxSession.objects.filter(key='CCFIT')
                    for number in num_max_users:
                        print(number.workout, 'THIS IS THE NUMBER COLLECTED')
                        #DO THE LOGIC TO CONTROL THE AMOUNT OF USERS
                        print(context[key]['session_number'])
                        count = Workout.objects.filter(date=self.request.session['value'], session_number=context[key]['session_number']).count()
                        print(count)
                        if count == number.workout:
                            context[key]['status'] = 'FULLY BOOKED'
                            context[key]['enable'] = True
                            print('FULLY BOOKED')

            elif booking_date_object < today_date_object:
                for key in context:
                    context[key]['expired'] = False
                #return to the user that
            else:
                for key in context:
                    print(' NOTHING 0-------------------0 ')
                    #Getting the number max of users per session and class from table MaxSession model
                    num_max_users = MaxSession.objects.filter(key='CCFIT')
                    for number in num_max_users:
                        print(number.workout, 'THIS IS THE NUMBER COLLECTED')
                        #DO THE LOGIC TO CONTROL THE AMOUNT OF USERS
                        print('I NEED THIS NUMBERRRRRRRRRRRRRR')
                        print(context[key]['session_number'])
                        count = Workout.objects.filter(date=self.request.session['value'], session_number=context[key]['session_number']).count()
                        print(count)
                        if count == number.workout:
                            context[key]['status'] = 'FULLY BOOKED'
                            context[key]['enable'] = True
                            print('FULLY BOOKED')

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


            print('-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-')
            print(context)

        return context

@method_decorator(user_all_classes, name='dispatch')
class PilatesView(LoginRequiredMixin, generic.TemplateView):
    model = Pilates
    template_name = "ccfit_app/pilates.html"

    def get_context_data(self, **kwargs):
        context = super(PilatesView, self).get_context_data(**kwargs)
        print('DO THE TIME SCHEME HERE for PILAATES')
        booked_flag = 'N'

        if 'value' in self.request.session:
            booking_date = self.request.session['value']
            print(booking_date)

            #BOOKING DATE
            booking_date_object = datetime.strptime(booking_date, '%Y-%m-%d').date()
            #print(type(booking_date_object))
            #print(booking_date_object)  # printed in default formatting

            #TODAY'S DATE
            today_date = datetime.today().strftime('%Y-%m-%d')
            today_date_object = datetime.strptime(today_date, '%Y-%m-%d').date()
            #print(type(today_date_object))
            context = {'session_1': {'start':'06:00', 'finish':'08:00', 'session_number': 1, 'expired':True,'status':'BOOK', 'enable':False},
                    'session_2': { 'start':'09:00', 'finish':'11:00', 'session_number': 2,  'expired':True, 'status':'BOOK', 'enable':False},
                    'session_3': { 'start':'12:00', 'finish':'14:00', 'session_number': 3,  'expired':True, 'status':'BOOK', 'enable':False},
                    'session_4': { 'start':'15:00', 'finish':'17:00', 'session_number': 4,  'expired':True, 'status':'BOOK', 'enable':False},
                    'session_5': { 'start':'18:00', 'finish':'20:00', 'session_number': 5,  'expired':True, 'status':'BOOK', 'enable':False},
                    'session_6': { 'start':'21:00', 'finish':'23:00', 'session_number': 6,  'expired':True, 'status':'BOOK', 'enable':False}}

            # IF HERE TO CHECK IF THERE IS ALREADY A BOOKING FOR THIS DAY
            print(self.request.user)
            print(self.request.session['value'])
            user = Pilates.objects.filter(email_user=self.request.user, date=self.request.session['value']).values('session_number')
            print('TOOK THE VALUE HEREEEEEEEEEEEEEEEEEE')
            print('DID SOMETHING NEW HEREEEEEEEEEEEEEEEEEEFDDDDDDDDFDFSD')
            print(user)
            if user.exists():
                booked_flag = 'Y'
                for course in user:
                    session_number_keep = course['session_number']
                    print(session_number_keep)
            ###############################################################
            ###############################################################
            print(booking_date_object)
            print(today_date_object)
            if booking_date_object == today_date_object:
                #do something
                print(time.strftime("%H:%M"))
                start_hour = time.strftime("%H")
                start_minute = time.strftime("%M")

                for key in context:
                    print(context[key]['start'])
                    schedule_date = context[key]['start']

                    start_time = (int(schedule_date[0:2])*60 + int(schedule_date[3:5])-30)
                    current_time =  datetime.now().hour*60 +datetime.now().minute
                    print(start_time, 'START TIME')
                    print(current_time , 'CURRENT TIME')
                    if start_time <= current_time:
                        context[key]['expired'] = False

                    #Getting the number max of users per session and class from table MaxSession model
                    num_max_users = MaxSession.objects.filter(key='CCFIT')
                    for number in num_max_users:
                        print(number.pilates, 'THIS IS THE NUMBER COLLECTED')
                        #DO THE LOGIC TO CONTROL THE AMOUNT OF USERS
                        print('I NEED THIS NUMBERRRRRRRRRRRRRR')
                        print(context[key]['session_number'])
                        count = Pilates.objects.filter(date=self.request.session['value'], session_number=context[key]['session_number']).count()
                        print(count)
                        if count == number.pilates:
                            context[key]['status'] = 'FULLY BOOKED'
                            context[key]['enable'] = True
                            print('FULLY BOOKED')


            elif booking_date_object < today_date_object:
                for key in context:
                    context[key]['expired'] = False
                #return to the user that
            else:
                for key in context:
                    print(' NOTHING 0-------------------0 ')
                    #Getting the number max of users per session and class from table MaxSession model
                    num_max_users = MaxSession.objects.filter(key='CCFIT')
                    for number in num_max_users:
                        print(number.pilates, 'THIS IS THE NUMBER COLLECTED')

                        #DO THE LOGIC TO CONTROL THE AMOUNT OF USERS
                        print('I NEED THIS NUMBERRRRRRRRRRRRRR')
                        print(context[key]['session_number'])
                        count = Pilates.objects.filter(date=self.request.session['value'], session_number=context[key]['session_number']).count()
                        print(count)
                        if count == number.pilates:
                            context[key]['status'] = 'FULLY BOOKED'
                            context[key]['enable'] = True
                            print('FULLY BOOKED')

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


            print('-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-')
            print(context)

        return context

@method_decorator(user_all_classes, name='dispatch')
class YogaView(LoginRequiredMixin, generic.TemplateView):
    model = Yoga
    template_name = "ccfit_app/yoga.html"

    def get_context_data(self, **kwargs):
        context = super(YogaView, self).get_context_data(**kwargs)
        print('DO THE TIME SCHEME HERE for PILAATES')
        booked_flag = 'N'

        if 'value' in self.request.session:
            booking_date = self.request.session['value']
            print(booking_date)

            #BOOKING DATE
            booking_date_object = datetime.strptime(booking_date, '%Y-%m-%d').date()
            #print(type(booking_date_object))
            #print(booking_date_object)  # printed in default formatting

            #TODAY'S DATE
            today_date = datetime.today().strftime('%Y-%m-%d')
            today_date_object = datetime.strptime(today_date, '%Y-%m-%d').date()
            #print(type(today_date_object))
            context = {'session_1': {'start':'06:00', 'finish':'08:00', 'session_number': 1, 'expired':True,'status':'BOOK', 'enable':False},
                    'session_2': { 'start':'09:00', 'finish':'11:00', 'session_number': 2,  'expired':True, 'status':'BOOK', 'enable':False},
                    'session_3': { 'start':'12:00', 'finish':'14:00', 'session_number': 3,  'expired':True, 'status':'BOOK', 'enable':False},
                    'session_4': { 'start':'15:00', 'finish':'17:00', 'session_number': 4,  'expired':True, 'status':'BOOK', 'enable':False},
                    'session_5': { 'start':'18:00', 'finish':'20:00', 'session_number': 5,  'expired':True, 'status':'BOOK', 'enable':False},
                    'session_6': { 'start':'21:00', 'finish':'23:00', 'session_number': 6,  'expired':True, 'status':'BOOK', 'enable':False}}

            # IF HERE TO CHECK IF THERE IS ALREADY A BOOKING FOR THIS DAY
            print(self.request.user)
            print(self.request.session['value'])
            user = Yoga.objects.filter(email_user=self.request.user, date=self.request.session['value']).values('session_number')
            print('TOOK THE VALUE HEREEEEEEEEEEEEEEEEEE')
            print('DID SOMETHING NEW HEREEEEEEEEEEEEEEEEEEFDDDDDDDDFDFSD')
            print(user)
            if user.exists():
                booked_flag = 'Y'
                for course in user:
                    session_number_keep = course['session_number']
                    print(session_number_keep)
            ###############################################################
            ###############################################################
            print(booking_date_object)
            print(today_date_object)
            if booking_date_object == today_date_object:
                #do something
                print(time.strftime("%H:%M"))
                start_hour = time.strftime("%H")
                start_minute = time.strftime("%M")

                for key in context:
                    print(context[key]['start'])
                    schedule_date = context[key]['start']

                    start_time = (int(schedule_date[0:2])*60 + int(schedule_date[3:5])-30)
                    current_time =  datetime.now().hour*60 +datetime.now().minute
                    print(start_time, 'START TIME')
                    print(current_time , 'CURRENT TIME')
                    if start_time <= current_time:
                        context[key]['expired'] = False

                    #Getting the number max of users per session and class from table MaxSession model
                    num_max_users = MaxSession.objects.filter(key='CCFIT')
                    for number in num_max_users:
                        print(number.yoga, 'THIS IS THE NUMBER COLLECTED')

                        #DO THE LOGIC TO CONTROL THE AMOUNT OF USERS
                        print('I NEED THIS NUMBERRRRRRRRRRRRRR')
                        print(context[key]['session_number'])
                        count = Yoga.objects.filter(date=self.request.session['value'], session_number=context[key]['session_number']).count()
                        print(count)
                        if count == number.yoga:
                            context[key]['status'] = 'FULLY BOOKED'
                            context[key]['enable'] = True
                            print('FULLY BOOKED')

            elif booking_date_object < today_date_object:
                for key in context:
                    context[key]['expired'] = False
                #return to the user that
            else:
                for key in context:
                    print(' NOTHING 0-------------------0 ')
                    #DO THE LOGIC TO CONTROL THE AMOUNT OF USERS
                    #Getting the number max of users per session and class from table MaxSession model
                    num_max_users = MaxSession.objects.filter(key='CCFIT')
                    for number in num_max_users:
                        print(number.yoga, 'THIS IS THE NUMBER COLLECTED')

                        print('I NEED THIS NUMBERRRRRRRRRRRRRR')
                        print(context[key]['session_number'])
                        count = Yoga.objects.filter(date=self.request.session['value'], session_number=context[key]['session_number']).count()
                        print(count)
                        if count == number.yoga:
                            context[key]['status'] = 'FULLY BOOKED'
                            context[key]['enable'] = True
                            print('FULLY BOOKED')

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


            print('-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-')
            print(context)

        return context

@method_decorator(user_all_classes, name='dispatch')
class SpinView(LoginRequiredMixin, generic.TemplateView):
    model = Spin
    template_name = "ccfit_app/spin.html"

    def get_context_data(self, **kwargs):
        context = super(SpinView, self).get_context_data(**kwargs)
        print('DO THE TIME SCHEME HERE for PILAATES')
        booked_flag = 'N'

        if 'value' in self.request.session:
            booking_date = self.request.session['value']
            print(booking_date)

            #BOOKING DATE
            booking_date_object = datetime.strptime(booking_date, '%Y-%m-%d').date()
            #print(type(booking_date_object))
            #print(booking_date_object)  # printed in default formatting

            #TODAY'S DATE
            today_date = datetime.today().strftime('%Y-%m-%d')
            today_date_object = datetime.strptime(today_date, '%Y-%m-%d').date()
            #print(type(today_date_object))
            context = {'session_1': {'start':'06:00', 'finish':'08:00', 'session_number': 1, 'expired':True,'status':'BOOK', 'enable':False},
                    'session_2': { 'start':'09:00', 'finish':'11:00', 'session_number': 2,  'expired':True, 'status':'BOOK', 'enable':False},
                    'session_3': { 'start':'12:00', 'finish':'14:00', 'session_number': 3,  'expired':True, 'status':'BOOK', 'enable':False},
                    'session_4': { 'start':'15:00', 'finish':'17:00', 'session_number': 4,  'expired':True, 'status':'BOOK', 'enable':False},
                    'session_5': { 'start':'18:00', 'finish':'20:00', 'session_number': 5,  'expired':True, 'status':'BOOK', 'enable':False},
                    'session_6': { 'start':'21:00', 'finish':'23:00', 'session_number': 6,  'expired':True, 'status':'BOOK', 'enable':False}}

            # IF HERE TO CHECK IF THERE IS ALREADY A BOOKING FOR THIS DAY
            print(self.request.user)
            print(self.request.session['value'])
            user = Spin.objects.filter(email_user=self.request.user, date=self.request.session['value']).values('session_number')
            print('TOOK THE VALUE HEREEEEEEEEEEEEEEEEEE')
            print('DID SOMETHING NEW HEREEEEEEEEEEEEEEEEEEFDDDDDDDDFDFSD')
            print(user)
            if user.exists():
                booked_flag = 'Y'
                for course in user:
                    session_number_keep = course['session_number']
                    print(session_number_keep)
            ###############################################################
            ###############################################################
            print(booking_date_object)
            print(today_date_object)
            if booking_date_object == today_date_object:
                #do something
                print(time.strftime("%H:%M"))
                start_hour = time.strftime("%H")
                start_minute = time.strftime("%M")

                for key in context:
                    print(context[key]['start'])
                    schedule_date = context[key]['start']

                    start_time = (int(schedule_date[0:2])*60 + int(schedule_date[3:5])-30)
                    current_time =  datetime.now().hour*60 +datetime.now().minute
                    print(start_time, 'START TIME')
                    print(current_time , 'CURRENT TIME')
                    if start_time <= current_time:
                        context[key]['expired'] = False

                    #Getting the number max of users per session and class from table MaxSession model
                    num_max_users = MaxSession.objects.filter(key='CCFIT')
                    for number in num_max_users:
                        print(number.spin, 'THIS IS THE NUMBER COLLECTED')

                        #DO THE LOGIC TO CONTROL THE AMOUNT OF USERS
                        print('I NEED THIS NUMBERRRRRRRRRRRRRR')
                        print(context[key]['session_number'])
                        count = Spin.objects.filter(date=self.request.session['value'], session_number=context[key]['session_number']).count()
                        print(count)
                        if count == number.spin:
                            context[key]['status'] = 'FULLY BOOKED'
                            context[key]['enable'] = True
                            print('FULLY BOOKED')




            elif booking_date_object < today_date_object:
                for key in context:
                    context[key]['expired'] = False
                #return to the user that
            else:
                for key in context:
                    print(' NOTHING 0-------------------0 ')
                    #DO THE LOGIC TO CONTROL THE AMOUNT OF USERS
                    #Getting the number max of users per session and class from table MaxSession model
                    num_max_users = MaxSession.objects.filter(key='CCFIT')
                    for number in num_max_users:
                        print(number.spin, 'THIS IS THE NUMBER COLLECTED')

                        print('I NEED THIS NUMBERRRRRRRRRRRRRR')
                        print(context[key]['session_number'])
                        count = Spin.objects.filter(date=self.request.session['value'], session_number=context[key]['session_number']).count()
                        print(count)
                        if count == number.spin:
                            context[key]['status'] = 'FULLY BOOKED'
                            context[key]['enable'] = True
                            print('FULLY BOOKED')

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


            print('-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-')
            print(context)

        return context

@method_decorator(user_all_classes, name='dispatch')
class JumpView(LoginRequiredMixin, generic.TemplateView):
    model = Jump
    template_name = "ccfit_app/jump.html"

    def get_context_data(self, **kwargs):
        context = super(JumpView, self).get_context_data(**kwargs)
        print('DO THE TIME SCHEME HERE for PILAATES')
        booked_flag = 'N'

        if 'value' in self.request.session:
            booking_date = self.request.session['value']
            print(booking_date)

            #BOOKING DATE
            booking_date_object = datetime.strptime(booking_date, '%Y-%m-%d').date()
            #print(type(booking_date_object))
            #print(booking_date_object)  # printed in default formatting

            #TODAY'S DATE
            today_date = datetime.today().strftime('%Y-%m-%d')
            today_date_object = datetime.strptime(today_date, '%Y-%m-%d').date()
            #print(type(today_date_object))
            context = {'session_1': {'start':'06:00', 'finish':'08:00', 'session_number': 1, 'expired':True,'status':'BOOK', 'enable':False},
                    'session_2': { 'start':'09:00', 'finish':'11:00', 'session_number': 2,  'expired':True, 'status':'BOOK', 'enable':False},
                    'session_3': { 'start':'12:00', 'finish':'14:00', 'session_number': 3,  'expired':True, 'status':'BOOK', 'enable':False},
                    'session_4': { 'start':'15:00', 'finish':'17:00', 'session_number': 4,  'expired':True, 'status':'BOOK', 'enable':False},
                    'session_5': { 'start':'18:00', 'finish':'20:00', 'session_number': 5,  'expired':True, 'status':'BOOK', 'enable':False},
                    'session_6': { 'start':'21:00', 'finish':'23:00', 'session_number': 6,  'expired':True, 'status':'BOOK', 'enable':False}}
            # IF HERE TO CHECK IF THERE IS ALREADY A BOOKING FOR THIS DAY
            print(self.request.user)
            print(self.request.session['value'])
            user = Jump.objects.filter(email_user=self.request.user, date=self.request.session['value']).values('session_number')
            print('TOOK THE VALUE HEREEEEEEEEEEEEEEEEEE')
            print('DID SOMETHING NEW HEREEEEEEEEEEEEEEEEEEFDDDDDDDDFDFSD')
            print(user)
            if user.exists():
                booked_flag = 'Y'
                for course in user:
                    session_number_keep = course['session_number']
                    print(session_number_keep)
            ###############################################################
            ###############################################################
            print(booking_date_object)
            print(today_date_object)
            if booking_date_object == today_date_object:
                #do something
                print(time.strftime("%H:%M"))
                start_hour = time.strftime("%H")
                start_minute = time.strftime("%M")
                for key in context:
                    print(context[key]['start'])
                    schedule_date = context[key]['start']
                    start_time = (int(schedule_date[0:2])*60 + int(schedule_date[3:5])-30)
                    current_time =  datetime.now().hour*60 +datetime.now().minute
                    print(start_time, 'START TIME')
                    print(current_time , 'CURRENT TIME')
                    if start_time <= current_time:
                        context[key]['expired'] = False
                    #DO THE LOGIC TO CONTROL THE AMOUNT OF USERS
                    #Getting the number max of users per session and class from table MaxSession model
                    num_max_users = MaxSession.objects.filter(key='CCFIT')
                    for number in num_max_users:
                        print(number.jump, 'THIS IS THE NUMBER COLLECTED')

                        print('I NEED THIS NUMBERRRRRRRRRRRRRR')
                        print(context[key]['session_number'])
                        count = Jump.objects.filter(date=self.request.session['value'], session_number=context[key]['session_number']).count()
                        print(count)
                        if count == number.jump:
                            context[key]['status'] = 'FULLY BOOKED'
                            context[key]['enable'] = True
                            print('FULLY BOOKED')
            elif booking_date_object < today_date_object:
                for key in context:
                    context[key]['expired'] = False
                #return to the user that
            else:
                for key in context:
                    print(' NOTHING 0-------------------0 ')
                    #DO THE LOGIC TO CONTROL THE AMOUNT OF USERS
                    #Getting the number max of users per session and class from table MaxSession model
                    num_max_users = MaxSession.objects.filter(key='CCFIT')
                    for number in num_max_users:
                        print(number.jump, 'THIS IS THE NUMBER COLLECTED')

                        print('I NEED THIS NUMBERRRRRRRRRRRRRR')
                        print(context[key]['session_number'])
                        count = Jump.objects.filter(date=self.request.session['value'], session_number=context[key]['session_number']).count()
                        print(count)
                        if count == number.jump:
                            context[key]['status'] = 'FULLY BOOKED'
                            context[key]['enable'] = True
                            print('FULLY BOOKED')
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
            print('-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-')
            print(context)
        return context

def cancelling_allclases(request):
    print('it got into the cancelling_allclases function', request)
    program_date = datetime.strptime(request.session['value'], '%Y-%m-%d').date()
    print(program_date)
    print('cancellllllllllllllling')
    invoice = Invoice.objects.get(email=request.user, from_date__lte=program_date, to_date__gte=program_date, type="MONTHLY PAYMENT")
    models = [Workout, Pilates, Spin, Yoga, Jump]
    found_other_bookings = True
    for model in models:
        number_bookings = model.objects.filter(email_user=request.user, date__gte=invoice.from_date)
        print(number_bookings, 'number_bookingsssssssssssssssssssssssssssss', str(model))
        if number_bookings.exists():
            print('FIRST LOOP')
            number_bookings = model.objects.filter(email_user=request.user, date__lte=invoice.to_date)
            if number_bookings.exists():
                print('BOOKING FOUNDDDDDDDDDDDDDDDDDDDDDD D D D D D D D D D D D D ')
                print(str(model))
                found_other_bookings = False
                break
    if found_other_bookings == True:
        print('DELETED THE VALUEEEEE')
        invoice.delete()

def invoice_insertion(request):
	#DO THE INVOICE INSERTION
	print('it got here', request)
	verify_enrollment = Invoice.objects.filter(email=request.user, type='MONTHLY PAYMENT')
	print(verify_enrollment)
	if not verify_enrollment.exists():
		user = UserProfileInfo.objects.get(email=request.user)
		print(user.membership)
		cost = 35
		if user.active == 'WORKOUT ONLY':
			cost = 35
		else:
			cost = 50
		verify = Invoice.objects.get(email=request.user, type='ENROLLMENT FEE')
		p = Invoice(email=request.user,from_date=verify.from_date,to_date=verify.to_date,year=verify.year,cost=cost,type="MONTHLY PAYMENT",status="GENERATE")
		p.save(force_insert=True)
	else:
		today_date_object = datetime.strptime(request.session['value'], '%Y-%m-%d').date()
		currentYear = int(datetime.now().year)
		print(request.user)
		print(today_date_object)
		print(currentYear)
		verify_month = Invoice.objects.filter(email=request.user, from_date__lte=today_date_object, to_date__gte=today_date_object, type="MONTHLY PAYMENT", year=currentYear)
		print(verify_month)
		if verify_month.exists():
			# DOESNT DO ANYTHING
			# ONLY CHECKS IF THE USER CHANGED THE enrollment
			# FROM WORKOUT ONLY TO ALL CLASSES
			user = UserProfileInfo.objects.get(email=request.user)
			if user.active == 'ALL CLASSES':
				update_invoice = Invoice.objects.get(email=request.user, from_date__lte=today_date_object, to_date__gte=today_date_object, type="MONTHLY PAYMENT", year=currentYear)
				update_invoice.cost = 50
				update_invoice.save()
			print('verying if the range is correcccccccccccccccct')
		else:
			flag_found = True
			dates = Invoice.objects.get(email=request.user, type="ENROLLMENT FEE")
			year = dates.year
			to_date_invoice = dates.to_date
			while flag_found:
				#GETS THE ENROLLMENT DATE AS A PARAMETER TO MAKE THE COUNTING FOR FINDING OUT THE NEW MONTH
				#from_30days = str(dates.from_date + timedelta(days = 30))
				from_1day = str(to_date_invoice + timedelta(days = 1))
				from_sameday = datetime.strptime(from_1day, '%Y-%m-%d').date()
				print(from_sameday, 'from_sameday')
				print(type(from_sameday))
				to_30days = str(from_sameday + timedelta(days = 30))
				to_30d_date = datetime.strptime(to_30days, '%Y-%m-%d').date()
				print(to_30d_date, 'to_30d_date')
				print(type(to_30d_date))
				date_booked = datetime.strptime(request.session['value'], '%Y-%m-%d').date()
				print(date_booked, 'date_booked')
				if date_booked >= from_sameday and date_booked <= to_30d_date:
					print('FOUUUUUUUUUUUUUUUNNNNNnnnnnnnnnnnnnnnnnnnnnnnnnnnnnNNNNNNNNND')
					user = UserProfileInfo.objects.get(email=request.user)
					cost = 35
					if user.active == 'WORKOUT ONLY':
						cost = 35
					else:
						cost = 50
					p = Invoice(email=request.user,from_date=from_sameday,to_date=to_30d_date,year=year,cost=cost,type="MONTHLY PAYMENT",status="GENERATE")
					p.save(force_insert=True)
					flag_found = False
				else:
					print('KEEEP LOOOOOOOOOOoooooooooooooooooooooooooooooooooooooooooOOPIG')
					print(to_date_invoice)
					print(to_date_invoice)
					to_date_invoice = to_30d_date
			print('verying if the range is WROOOOOOOOOOOONGGGGGG')


@login_required
def Check_Booking_jump(request, session):
    cancel = Jump.objects.filter(email_user=request.user, date=request.session['value'], session_number=session)
    print('CHECKING')
    if cancel.exists():
        print('IT EXISTS, I WANT TO CANCEL')
        cancel.delete()
        cancelling_allclases(request)
        context = {'response': 'cancelled'}
        return render(request, 'ccfit_app/confirmation.html', context)
    else:
        flag_found = False
        models = [Workout, Pilates, Spin, Yoga, Jump]
        for model in models:
            #print(model, 'PRINTING MODEL')
            #print(type(model), 'PRINTING TYPE MODEL')
            found_booking = model.objects.filter(email_user=request.user, date=request.session['value'])
            if found_booking.exists():
                print('BOOKING FOUNDDDDDDDDDDDDDD')
                flag_found = True
        if not flag_found:
            for n in range(1,7):
                if session == str(n):
                    print('#check on the table ', n,' HERE ###############################')
                    booking = Jump(date=request.session['value'], email_user=request.user, session_number=session)
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
                            print(email_user)
                            message = 'Dear ' + str(request.user) + '\nThank you for booking the JUMP session with CCFIT. \nYour booking is now confirmed for: ' + str(request.session['value']) + ' \nStart Time '+ start + ' - ' + 'End Time ' + finish
                            send_mail('CCFIT Jump CLASS - Booking Confirmation', message, 'ccfitgym@gmail.com', [email_user], fail_silently=False)
            context = {'response': 'Confirmed'}
            booking.save()
        else:
            context = {'response': 'YOU CANNOT BOOK'}
        return render(request, 'ccfit_app/confirmation.html', context)



@login_required
def Check_Booking_spin(request, session):
    cancel = Spin.objects.filter(email_user=request.user, date=request.session['value'], session_number=session)
    print('CHECKING')
    if cancel.exists():
        print('IT EXISTS, I WANT TO CANCEL')
        cancel.delete()
        cancelling_allclases(request)
        context = {'response': 'cancelled'}
        return render(request, 'ccfit_app/confirmation.html', context)
    else:
        flag_found = False
        models = [Workout, Pilates, Spin, Yoga, Jump]
        for model in models:
            found_booking = model.objects.filter(email_user=request.user, date=request.session['value'])
            if found_booking.exists():
                print('BOOKING FOUNDDDDDDDDDDDDDD')
                flag_found = True
        if not flag_found:
            for n in range(1,7):
                if session == str(n):
                    print('#check on the table ', n,' HERE ###############################')
                    booking = Spin(date=request.session['value'], email_user=request.user, session_number=session)
                    context = {'session_1': {'start':'06:00', 'finish':'08:00', 'session_number': 1, 'expired':True,'status':'BOOK', 'enable':False},
                            'session_2': { 'start':'09:00', 'finish':'11:00', 'session_number': 2,  'expired':True, 'status':'BOOK', 'enable':False},
                            'session_3': { 'start':'12:00', 'finish':'14:00', 'session_number': 3,  'expired':True, 'status':'BOOK', 'enable':False},
                            'session_4': { 'start':'15:00', 'finish':'17:00', 'session_number': 4,  'expired':True, 'status':'BOOK', 'enable':False},
                            'session_5': { 'start':'18:00', 'finish':'20:00', 'session_number': 5,  'expired':True, 'status':'BOOK', 'enable':False},
                            'session_6': { 'start':'21:00', 'finish':'23:00', 'session_number': 6,  'expired':True, 'status':'BOOK', 'enable':False}}
                    invoice_insertion(request)
                    print('call the spin hereeeeeeeeeeeee')
                    for key in context:
                        if session == str(context[key]['session_number']):
                            start = context[key]['start']
                            finish = context[key]['finish']
                            email_user = str(request.user)
                            print(email_user)
                            message = 'Dear ' + str(request.user) + '\nThank you for booking the Spin session with CCFIT. \nYour booking is now confirmed for: ' + str(request.session['value']) + ' \nStart Time '+ start + ' - ' + 'End Time ' + finish
                            send_mail('CCFIT Spin CLASS - Booking Confirmation', message, 'ccfitgym@gmail.com', [email_user], fail_silently=False)
            context = {'response': 'Confirmed'}
            booking.save()
        else:
            context = {'response': 'YOU CANNOT BOOK'}
        return render(request, 'ccfit_app/confirmation.html', context)



@login_required
def Check_Booking_yoga(request, session):
    cancel = Yoga.objects.filter(email_user=request.user, date=request.session['value'], session_number=session)
    print('CHECKING')
    if cancel.exists():
        print('IT EXISTS, I WANT TO CANCEL')
        cancel.delete()
        cancelling_allclases(request)
        context = {'response': 'cancelled'}
        return render(request, 'ccfit_app/confirmation.html', context)
    else:
        flag_found = False
        models = [Workout, Pilates, Spin, Yoga, Jump]
        for model in models:
            found_booking = model.objects.filter(email_user=request.user, date=request.session['value'])
            if found_booking.exists():
                print('BOOKING FOUNDDDDDDDDDDDDDD')
                flag_found = True
        if not flag_found:
            for n in range(1,7):
                if session == str(n):
                    print('#check on the table ', n,' HERE ###############################')
                    booking = Yoga(date=request.session['value'], email_user=request.user, session_number=session)
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
                            print(email_user)
                            message = 'Dear ' + str(request.user) + '\nThank you for booking the Yoga session with CCFIT. \nYour booking is now confirmed for: ' + str(request.session['value']) + ' \nStart Time '+ start + ' - ' + 'End Time ' + finish
                            send_mail('CCFIT Yoga CLASS - Booking Confirmation', message, 'ccfitgym@gmail.com', [email_user], fail_silently=False)
            context = {'response': 'Confirmed'}
            booking.save()
        else:
            context = {'response': 'YOU CANNOT BOOK'}
        return render(request, 'ccfit_app/confirmation.html', context)



@login_required
def Check_Booking_pilates(request, session):
    cancel = Pilates.objects.filter(email_user=request.user, date=request.session['value'], session_number=session)
    print('CHECKING')
    if cancel.exists():
        print('IT EXISTS, I WANT TO CANCEL')
        cancel.delete()
        cancelling_allclases(request)
        context = {'response': 'cancelled'}
        return render(request, 'ccfit_app/confirmation.html', context)
    else:
        flag_found = False
        models = [Workout, Pilates, Spin, Yoga, Jump]
        for model in models:
            found_booking = model.objects.filter(email_user=request.user, date=request.session['value'])
            if found_booking.exists():
                print('BOOKING FOUNDDDDDDDDDDDDDD')
                flag_found = True
        if not flag_found:
            for n in range(1,7):
                if session == str(n):
                    print('#check on the table ', n,' HERE ###############################')
                    booking = Pilates(date=request.session['value'], email_user=request.user, session_number=session)
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
                            print(email_user)
                            message = 'Dear ' + str(request.user) + '\nThank you for booking the Pilates session with CCFIT. \nYour booking is now confirmed for: ' + str(request.session['value']) + ' \nStart Time '+ start + ' - ' + 'End Time ' + finish
                            send_mail('CCFIT Pilates CLASS - Booking Confirmation', message, 'ccfitgym@gmail.com', [email_user], fail_silently=False)
            context = {'response': 'Confirmed'}
            booking.save()
        else:
            context = {'response': 'YOU CANNOT BOOK'}
        return render(request, 'ccfit_app/confirmation.html', context)




@login_required
def Check_Booking_workout(request, session):
    cancel = Workout.objects.filter(email_user=request.user, date=request.session['value'], session_number=session)
    print('CHECKING')
    if cancel.exists():
        print('IT EXISTS, I WANT TO CANCEL')
        cancel.delete()
		# VERIFICAR TODOS OS BOOKINGS
        user = UserProfileInfo.objects.get(email=request.user)
        if user.active == 'WORKOUT ONLY':
	        program_date = datetime.strptime(request.session['value'], '%Y-%m-%d').date()
	        print(program_date)
	        invoice = Invoice.objects.get(email=request.user, from_date__lte=program_date, to_date__gte=program_date, type="MONTHLY PAYMENT")
	        number_bookings = Workout.objects.filter(email_user=request.user, date__gte=invoice.from_date)
	        print(number_bookings, 'number_bookingsssssssssssssssssssssssssssss')
	        if number_bookings.exists():
	            number_bookings = Workout.objects.filter(email_user=request.user, date__lte=invoice.to_date)
	            if number_bookings.exists():
	                print('BOOKING NOT FOUNDDDDDDDDDDDDDDDDDDDDDD D D D D D D D D D D D D ')
	            else:
	                print('deleted dddddddddddddd d d d d d d  dd dddddddddddddddddd d d')
	                invoice.delete()
	        else:
	            invoice.delete()
        else:
            cancelling_allclases(request)
                # break
			# END FOR
		# DO THE SUBTRACTION OF THE TABLE FROM HERE
        context = {'response': 'cancelled'}
        return render(request, 'ccfit_app/confirmation.html', context)
    else:
        flag_found = False
        models = [Workout, Pilates, Spin, Yoga, Jump]
        for model in models:
            found_booking = model.objects.filter(email_user=request.user, date=request.session['value'])
            if found_booking.exists():
                print('BOOKING FOUNDDDDDDDDDDDDDD')
                flag_found = True
        if not flag_found:
            for n in range(1,7):
                if session == str(n):
                    print('#check on the table ', n,' HERE ###############################')
                    booking = Workout(date=request.session['value'], email_user=request.user, session_number=session)
                    context = {'session_1': {'start':'06:00', 'finish':'08:00', 'session_number': 1, 'expired':True,'status':'BOOK', 'enable':False},
                            'session_2': { 'start':'09:00', 'finish':'11:00', 'session_number': 2,  'expired':True, 'status':'BOOK', 'enable':False},
                            'session_3': { 'start':'12:00', 'finish':'14:00', 'session_number': 3,  'expired':True, 'status':'BOOK', 'enable':False},
                            'session_4': { 'start':'15:00', 'finish':'17:00', 'session_number': 4,  'expired':True, 'status':'BOOK', 'enable':False},
                            'session_5': { 'start':'18:00', 'finish':'20:00', 'session_number': 5,  'expired':True, 'status':'BOOK', 'enable':False},
                            'session_6': { 'start':'21:00', 'finish':'23:00', 'session_number': 6,  'expired':True, 'status':'BOOK', 'enable':False}}

                    invoice_insertion(request)
						# checar primeiro se ja tem invoice pra isso senao gerar um novo

                    #else:
                    #    passworddd=1
                    #    verify_enrollment = Invoice.objects.get(email=request.user, type='ENROLLMENT FEE')
                    #    verify_enrollment.status = 'PAID'
                    #    verify_enrollment.save()
                    for key in context:
                        if session == str(context[key]['session_number']):
                            start = context[key]['start']
                            finish = context[key]['finish']
                            email_user = str(request.user)
                            print(email_user)
                            message = 'Dear ' + str(request.user) + '\nThank you for booking the Workout session with CCFIT. \nYour booking is now confirmed for: ' + str(request.session['value']) + ' \nStart Time '+ start + ' - ' + 'End Time ' + finish
                            send_mail('CCFIT Workout CLASS - Booking Confirmation', message, 'ccfitgym@gmail.com', [email_user], fail_silently=False)
            context = {'response': 'Confirmed'}
            booking.save()
        else:
            context = {'response': 'YOU CANNOT BOOK'}
        return render(request, 'ccfit_app/confirmation.html', context)

@login_required
def BookingPage(request):
    #form_class = ExampleForm
    #success_url = reverse_lazy('ccfit:index')
    #template_name = "ccfit_app/booking_page.html"
    form = ExampleForm()
    return render(request, 'ccfit_app/booking_page.html', {'form':form})

@login_required
@admin_only
def CheckingPage(request):
    #form_class = ExampleForm
    #success_url = reverse_lazy('ccfit:index')
    #template_name = "ccfit_app/booking_page.html"
    form = ExampleForm()
    return render(request, 'ccfit_app/check_classes.html', {'form':form})



class CreateProfilePageView(LoginRequiredMixin, CreateView):
    model = UserProfileInfo
    form_class = ProfilePageForm
    template_name = "ccfit_app/create_user_profile_page.html"
    #success_url = reverse_lazy('ccfit:index')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class EditProfilePageView(LoginRequiredMixin, generic.UpdateView):
    model = UserProfileInfo
    template_name = "ccfit_app/edit_profile_page.html"
    #fields = ['nickname', 'gender', 'birth_date', 'address1', 'address2', 'county', 'country', 'prefix', 'phone']
    form_class = ProfilePageForm
    success_url = reverse_lazy('ccfit:index')


    def get(self, request, pk):
        print(pk, 've se imprime pkkkkkkkkkkkkkk')
        #currentYear = int(datetime.now().year)
        #print(currentYear)
        #print(type(currentYear))
        #date = today_date = datetime.today().strftime('%Y-%m-%d')
        #print(date)
        #print(type(date))
        obj = get_object_or_404(UserProfileInfo, pk = pk)
        form = ProfilePageForm(instance = obj)
        return render(request, 'ccfit_app/edit_profile_page.html', {
        'form': form
    })

    def post(self, request, pk):
        print("POST METHOD")
        obj = get_object_or_404(UserProfileInfo, pk = pk)
        form = ProfilePageForm(data=request.POST, instance = obj)
        print(form.is_valid())
        if  form.is_valid():
            print('got here')
            profile = form.save(commit=False)
            profile.registration_completed = True
            profile.active = profile.membership
            today_date = datetime.today().strftime('%Y-%m-%d')
            today_date_object = datetime.strptime(today_date, '%Y-%m-%d').date()
            currentYear = int(datetime.now().year)
            verify_enrollment = Invoice.objects.filter(email=profile.email, type='ENROLLMENT FEE')
			# future_30days = str(today_date_object + stimedelta(days = 30))
            future_30days=str(today_date_object + timedelta(days = 30))
            print(future_30days, 'future_30days')
            future_30days = datetime.strptime(future_30days, '%Y-%m-%d').date()
			# print(future_30days, 'future_30days')
            if not verify_enrollment.exists():
	            p = Invoice(email=profile.email,
	            			 from_date=today_date_object,
							 to_date=future_30days,
	            			 year=currentYear,
	            			 cost=30,
	            			 type="ENROLLMENT FEE",
	            			 status="GENERATE")
	            p.save(force_insert=True)
            profile.save()
            return HttpResponseRedirect(reverse_lazy('ccfit:index'))
        else:
            print("FORMS NÃO VALIDOS")
            #return redirect('accounts:allUser')
            return HttpResponseRedirect(reverse_lazy('ccfit:index'))

class PasswordsChangeView(LoginRequiredMixin, PasswordChangeView):
    form_class = PasswordChangeForm
    template_name = "ccfit_app/change_password.html"
    success_url = reverse_lazy('ccfit:password_sucess')


@login_required
def password_sucess(request):
    return render(request, 'ccfit_app/password_sucess.html', {})


#class SignUp(generic.CreateView):
#    form_class = forms.SignUpForm
#    success_url = reverse_lazy('ccfit:index')
#    template_name = "ccfit_app/signup.html"
#    def form_valid(self, form):
#        #save the new user first
#        form.save()
#        email = self.request.POST['email']
#        password = self.request.POST['password1']
#        #authenticate user then loginx
#        user = authenticate(email=form.cleaned_data['email'], password=form.cleaned_data['password1'],)
#        login(self.request, user)
#        return HttpResponseRedirect(reverse_lazy('ccfit:index'))


def create_user(request):
    print('faz o request')
    if request.method=='POST':
        form = UserCreateForm(data=request.POST)
        profile_form = UserProfileInfoForm(data=request.POST)
        if form.is_valid() and profile_form.is_valid():
            user = form.save()
            user.save()
            profile = profile_form.save(commit=False)
            profile.email = user.email
            profile.user = user
            profile.save()
            email = request.POST['email']
            password = request.POST['password1']
            user = authenticate(email=form.cleaned_data['email'], password=form.cleaned_data['password1'])
            login(request, user)
            return HttpResponseRedirect(reverse_lazy('ccfit:index'))
    else:
        form = UserCreateForm()
        profile_form = UserProfileInfoForm()

    context = {'form': form, 'profile_form': profile_form}
    return render(request, 'ccfit_app/signup.html', context)




class EditProfile(LoginRequiredMixin, generic.UpdateView):
    form_class = forms.EditProfileForm
    success_url = reverse_lazy('ccfit:index')
    template_name = "ccfit_app/edit_profile.html"

    def get_object(self):
        return self.request.user


@login_required
def index(request):
	#user info
    user = UserProfileInfo.objects.filter(email=request.user)
    value_type = 'USER'
    registered = False
    status = 'PAID'
    status_mp = 'GENERATE'
    if user.exists():
        for course in user:
            value_type = course.type
            registered = course.registration_completed

	#invoice info
    verify_enrollment = Invoice.objects.filter(email=request.user, type='ENROLLMENT FEE')
    if verify_enrollment.exists():
        for course in verify_enrollment:
            print(course.status)
            status = course.status
    verify_enrollment_MP = Invoice.objects.filter(email=request.user, type='MONTHLY PAYMENT')
    if verify_enrollment_MP.exists():
        for course in verify_enrollment_MP:
            print(course.status)
            status_mp = course.status
            if status_mp == 'REQUESTED':
                break
    mydict = {'type': value_type, 'registration': registered, 'status': status, 'status_MP': status_mp}
    return render(request, 'ccfit_app/index.html', mydict)

@method_decorator(admin_only, name='dispatch')
class UsersListView(LoginRequiredMixin, ListView):
    print('TESTING')
    template_name = "ccfit_app/allUsers.html"
    model = UserProfileInfo
    context_object_name = "users"

    def get_queryset(self):
        print("FAZ A BUSCA PADRAO DO FILTRO")
        email = self.request.GET.get('search')
        print(email, 'thats the email')
        object_list = self.model.objects.all()
        print(object_list)
        if email:
            object_list = object_list.filter(email__contains=email)
        return object_list


@method_decorator(admin_only, name='dispatch')
class UsersUpdateView(LoginRequiredMixin, UpdateView):
    print('HEREEEEEEE')
    model = UserProfileInfo
    template_name = "ccfit_app/updateUsers.html"
    form_class = UserProfileInfoFormUsers
    success_url = reverse_lazy('ccfit:all_users')

    def get(self, request, pk):
        print(pk, 've se imprime pkkkkkkkkkkkkkk')
        obj = get_object_or_404(UserProfileInfo, pk = pk)
        form = UserProfileInfoFormUsers(instance = obj)
        return render(request, 'ccfit_app/updateUsers.html', {
        'form': form
    })

    def post(self, request, pk):
        print("POST METHOD")
        obj = get_object_or_404(UserProfileInfo, pk = pk)
        form = UserProfileInfoFormUsers(data=request.POST, instance = obj)
        print(form.is_valid())
        if  form.is_valid():
            system_user = User.objects.get(email=obj.email)
            print("if valido")
            type_user = obj.type
            print(type, 'returning type to see if is correct')
            if type_user == 'ADMINISTRATOR':
                system_user.is_superuser= True
                system_user.is_staff= True
                print("SUPERUSER DEFINED")
            else:
                system_user.is_superuser= False
                system_user.is_staff= False
                print("SUPERUSER = false")
            print('esse teste user')
            system_user.save()
            profile = form.save(commit=False)
            print(profile.membership, 'profile.membership')
            print(profile.active, 'profile.active')
            profile.membership = profile.active
            profile.save()
            return HttpResponseRedirect(reverse_lazy('ccfit:all_users'))
        else:
            print("FORMS NÃO VALIDOS")
            #return redirect('accounts:allUser')
            return HttpResponseRedirect(reverse_lazy('ccfit:all_users'))
