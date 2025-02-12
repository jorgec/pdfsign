from django.urls import path, include

from accounts.controllers.account.views import auth

urlpatterns = [
    path('logout', auth.LogoutView.as_view(), name="logout"),
    path('login', auth.LoginView.as_view(), name="login"),
    path('postlogin', auth.AccountPostLoginView.as_view(), name="postlogin"),
]
