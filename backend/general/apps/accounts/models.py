from mongoengine import Document, StringField, EmailField, BooleanField, DateTimeField
from mongoengine import (
    ReferenceField,
    DictField,
    DecimalField,
    CASCADE,
    NULLIFY,
    ListField,
)
import mongoengine
from django.utils import timezone
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.contrib.auth.hashers import make_password, check_password
import uuid

# Django ORM imports for blacklisted tokens
from django.db import models


# In mongoengine, we'll add these methods directly to the User class
# rather than using a separate manager


class User(Document):
    """User representation for Waterston Employee using MongoDB"""

    email = EmailField(required=True, unique=True)
    password = StringField(required=True)
    is_active = BooleanField(default=True)
    is_staff = BooleanField(default=False)  # For admin access
    is_superuser = BooleanField(default=False)
    date_joined = DateTimeField(default=timezone.now)
    last_login = DateTimeField(null=True)
    groups = ListField(StringField(), default=list)
    user_permissions = ListField(StringField(), default=list)

    # These fields make the User model compatible with Django's admin
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    # Flag to indicate this is a Django-compatible auth model
    is_authenticated = True
    is_anonymous = False

    meta = {
        "collection": "users",
        "indexes": [
            "email",
        ],
    }

    def __str__(self):
        return self.email

    def get_username(self):
        """Return the username for this User."""
        return self.email

    def get_full_name(self):
        """Return user's email as full name."""
        return self.email

    def get_short_name(self):
        """Return user's email as short name."""
        return self.email

    @property
    def id(self):
        """Return the primary key for this User."""
        return self.pk

    def save(self, *args, **kwargs):
        # Check if this document already exists in the database
        # If it doesn't have an ID yet, it's new
        is_new_document = not bool(self.id)

        if is_new_document:
            self.last_login = None

        super().save(*args, **kwargs)

    @classmethod
    def create_user(cls, email, password=None, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError("Users must have an email address")

        # Normalize email
        email = email.lower()

        # Create user
        user = cls(email=email, **extra_fields)
        user.set_password(password)
        user.save()

        return user

    @classmethod
    def create_superuser(cls, email, password=None, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        return cls.create_user(email, password, **extra_fields)

    def set_password(self, raw_password):
        """Set password with Django's password hashing."""
        if raw_password is None:
            self.password = make_password(None)
        else:
            self.password = make_password(raw_password)

    def check_password(self, raw_password):
        """Check if provided password matches stored password."""
        # Handle empty passwords
        if not raw_password or not self.password:
            return False

        # Use Django's password checking
        return check_password(raw_password, self.password)


@receiver(user_logged_in)
def update_last_login(sender, user, request, **kwargs):
    """
    Update last_login timestamp when user logs in
    """
    # For mongoengine documents, we need to modify and save
    user.last_login = timezone.now()
    user.save()


class EmployeeProfile(Document):
    """Essential employee information"""

    user = ReferenceField(User, reverse_delete_rule=CASCADE)
    employee_id = StringField(max_length=50, unique=True)
    first_name = StringField(max_length=100)
    last_name = StringField(max_length=100)
    department = StringField(max_length=100)
    position = StringField(max_length=100)
    manager = ReferenceField("self", reverse_delete_rule=NULLIFY, required=False)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.employee_id})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    meta = {"collection": "employee_profiles", "indexes": ["employee_id", "user"]}


class ExpenseSettings(Document):
    """Basic expense configuration"""

    CURRENCY_CHOICES = [
        ("GBP", "British Pound"),
        ("USD", "US Dollar"),
        ("EUR", "Euro"),
    ]

    user = ReferenceField(User, reverse_delete_rule=CASCADE)
    default_currency = StringField(
        max_length=3, choices=CURRENCY_CHOICES, default="GBP"
    )
    expense_approver = ReferenceField(User, reverse_delete_rule=NULLIFY, required=False)
    monthly_expense_limit = DecimalField(precision=2, required=False)

    def __str__(self):
        return f"Expense settings for {self.user.email}"

    meta = {"collection": "expense_settings", "indexes": ["user", "expense_approver"]}


# This model uses Django's ORM, not MongoEngine
class BlacklistedToken(models.Model):
    """
    Model for storing blacklisted JWT tokens in SQLite.
    This uses Django's ORM, not MongoEngine.
    """

    token_jti = models.CharField(max_length=255, unique=True)
    user_id = models.CharField(max_length=255, null=True, blank=True)
    blacklisted_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()

    class Meta:
        db_table = "blacklisted_tokens"
        indexes = [
            models.Index(fields=["token_jti"]),
            models.Index(fields=["user_id"]),
            models.Index(fields=["expires_at"]),
        ]

    @classmethod
    def is_blacklisted(cls, token_jti):
        """Check if a token JTI is blacklisted"""
        return cls.objects.filter(token_jti=token_jti).exists()

    @classmethod
    def clean_expired_tokens(cls):
        """Remove expired tokens from the blacklist"""
        cls.objects.filter(expires_at__lt=timezone.now()).delete()
