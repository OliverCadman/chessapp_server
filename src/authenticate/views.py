from rest_framework.generics import CreateAPIView
from authenticate.serializers import AuthUserSerializer
from django.contrib.auth import get_user_model


class SignupView(CreateAPIView):
    """
    Public-facing view to create new Auth User
    """

    queryset = get_user_model().objects.all()
    serializer_class = AuthUserSerializer
