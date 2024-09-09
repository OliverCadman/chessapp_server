from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser, 
    PermissionsMixin,
    BaseUserManager
    )


class UserManager(BaseUserManager):
    """
    Custom manager for User model. Creates regular users and super users.
    """

    def create_user(self, email: str, password: str = None, **extra_fields):
        """Create a regular user."""

        if not email:
            raise ValueError("Please provide an email address.")
        
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self.db)

        return user
    
    def create_superuser(self, email: str, password: str = None, **extra_fields):
        """Create superuser with staff and superuser status."""

        user = self.create_user(email, password, **extra_fields)
        user.is_superuser = True
        user.is_staff = True
        user.save(using=self.db)

        return user


# Create your models here.
class User(AbstractBaseUser, PermissionsMixin):

    email = models.EmailField(max_length=244, unique=True, null=False)
    name = models.CharField(max_length=255)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = "email"

    objects = UserManager()
