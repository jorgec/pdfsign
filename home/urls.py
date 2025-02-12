from django.urls import path, include

from home.views import LandingPageView

urlpatterns = [
    path('', LandingPageView.as_view(), name="home"),
]
