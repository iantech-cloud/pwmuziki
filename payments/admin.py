from django.contrib import admin
from .models import Invoice, Payout, Refund, Transaction
admin.site.register(Invoice)
admin.site.register(Transaction)
admin.site.register(Refund)
admin.site.register(Payout)
