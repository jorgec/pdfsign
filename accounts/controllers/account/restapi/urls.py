from django.urls import path

from accounts.controllers.account.restapi.main import login, register, CurrentLoggedInUser, check_email, check_username, relogin

urlpatterns = [
    path('login', login),
    path('register', register),
    path('relogin', relogin),
    path('user', CurrentLoggedInUser.as_view({'get': 'retrieve'}), name="current_user"),
    path('check_email', check_email),
    path('check_username', check_username)
]
