"""URL Mapping for Authentication API"""

from django.urls import path
from authenticate.views import SignupView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView
)

app_name = "authenticate"

urlpatterns = [
    path("sign-up/", SignupView.as_view(), name="sign-up"),
    path('token/', TokenObtainPairView.as_view(), name="claim-token"),
    path('token/refresh', TokenRefreshView.as_view(), name="refresh-token")
]
