from django.contrib import admin
from django.contrib.auth.models import Group, Permission

from .models import Account
from .models.account.admin import UserAdmin

# Now register the new SubscriptionAdmin...
admin.site.register(Account, UserAdmin)

admin.site.unregister(Group)
