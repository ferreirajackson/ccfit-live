import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", 'ccfit_project.settings')

import django
django.setup()

from ccfit_app.models import Booking
from faker import Faker

fakegen = Faker()

def populate(N=5):
    for entry in range(N):
        fake_name = fakegen.name()
        fake_id = fakegen.random_int()
        fake_amount = fakegen.random_int()

        book = Booking.objects.get_or_create(id_booking=fake_id, amount=fake_amount, name=fake_name)[0]


if __name__ == '__main__':
    print("POPULATING DATABASE")
    populate(20)
    print('COMPLETED')
