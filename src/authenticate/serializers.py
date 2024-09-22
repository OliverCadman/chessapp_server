from rest_framework import serializers
from django.contrib.auth import get_user_model

import re


class AuthUserSerializer(serializers.ModelSerializer):
    """
    Serializer for the Auth User Model.

    Validates, creates and updates users.
    """

    password1 = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = get_user_model()
        fields = (
            "id", "email", "password1", "password2",
        )

    def validate(self, data): 
        """
        Regex check if passwords contain:
            - At least one uppercase character
            - At least one special character
            - At least one number

        Check if both passwords match.
        """

        errors = {}

        regex = r"^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$"
        if not re.match(regex, data["password1"]) or not re.match(regex, data["password2"]):
            errors["weak_password"] = (
                "Passwords must contain at least 8 characters, " 
                "one uppercase letter, one number and one special character.")

        if data["password1"] != data["password2"]:
            errors["password_mismatch"] = "Passwords must match."
        
        if errors:
            raise serializers.ValidationError(errors)
        
        return data

    def create(self, validated_data):
        """
        Creates a new Auth User instance, using validated data
        returned from the validation method.

        Data dict only contains email, and is then supplemented
        with the validated password.
        """
        data = {
            key: value for key, value in validated_data.items()
            if key not in ("password1", "password2")
        }

        data["password"] = validated_data["password1"]

        return self.Meta.model.objects.create_user(**data)
