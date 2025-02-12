from django.contrib import messages
from django.contrib.auth import logout, authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View

from accounts.models.account.forms import LoginForm
from common_core.controllers.scaffold import ControllerScaffold

class LogoutView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        logout(request)
        return redirect(reverse('home'))


class AccountPostLoginView(View):
    """
    Post-login actions performed after authentication by allauth
    Place all user-type specific actions here (e.g. redirections, logging)
    """

    def get(self, request, *args, **kwargs):
        try:
            if request.user.is_admin:
                return HttpResponseRedirect("admin")
            else:
                return HttpResponseRedirect(reverse("home"))

        except AttributeError:
            return HttpResponseRedirect(reverse("login"))


class LoginView(ControllerScaffold, View):
    def get(self, request, *args, **kwargs):
        form = LoginForm()

        context = {
            "form": form
        }

        return render(request, 'login.html', context)

    def post(self, request, *args, **kwargs):
        form = LoginForm(data=request.POST)

        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')

            user = authenticate(username=username, password=password)

            if user is not None:
                if not user.is_active:
                    messages.error(
                        request, "User account is not active", extra_tags="warning"
                    )
                else:
                    login(request, user)
                    messages.success(request, f"Welcome, {user}!", extra_tags="success")

                    url = reverse('postlogin')
                    return HttpResponseRedirect(url)
            else:
                messages.error(request, "Invalid credentials", extra_tags="warning")
        else:
            messages.error(request, form.errors, extra_tags="warning")

        context = {
            "form": form,
        }
        return render(request, "login.html", context)
