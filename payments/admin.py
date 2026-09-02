from django.contrib import admin
from .models import Invoice, Transaction
admin.site.register(Invoice)
admin.site.register(Transaction)
