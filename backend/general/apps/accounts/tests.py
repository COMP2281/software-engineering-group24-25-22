from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
import jwt
from datetime import datetime, timedelta
import json
from django.conf import settings

from .models import User, EmployeeProfile, BlacklistedToken


class JWTAuthenticationTests(TestCase):
    """Test JWT authentication functionality"""

    def setUp(self):
        """Set up test data and client"""
        self.client = APIClient()
        self.register_url = "/api/auth/register/"
        self.login_url = "/api/auth/token/"
        self.refresh_url = "/api/auth/token/refresh/"
        self.logout_url = "/api/auth/logout/"
        self.user_url = "/api/auth/user/"

        # Test user data with timestamp to ensure unique email
        import time

        timestamp = int(time.time())

        self.user_data = {
            "email": f"testuser_{timestamp}@example.com",
            "password": "test_password123",
            "password2": "test_password123",
            "first_name": "Test",
            "last_name": "User",
            "department": "Engineering",
            "position": "Developer",
        }

        # Generate unique email for the existing user
        self.existing_email = f"existinguser_{timestamp}@example.com"

        # Check if user exists and delete if it does
        existing_user = User.objects(email=self.existing_email).first()
        if existing_user:
            existing_user.delete()

        # Create test user directly for some tests
        self.test_user = User.create_user(
            email=self.existing_email, password="existing_password123"
        )

        # Create an employee profile for the test user
        employee_id = str(EmployeeProfile.objects.count() + 1)
        self.profile = EmployeeProfile(
            user=self.test_user,
            employee_id=employee_id,
            first_name="Existing",
            last_name="User",
            department="Testing",
            position="Tester",
        )
        self.profile.save()

    def test_user_registration(self):
        """Test user registration with employee profile creation"""
        response = self.client.post(self.register_url, self.user_data, format="json")

        # Check the response
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("refresh", response.data)
        self.assertIn("access", response.data)
        self.assertIn("user", response.data)

        # Check that user was created
        user_exists = User.objects(email=self.user_data["email"]).first() is not None
        self.assertTrue(user_exists)

        # Check that employee profile was created
        user = User.objects(email=self.user_data["email"]).first()
        profile_exists = EmployeeProfile.objects(user=user).first() is not None
        self.assertTrue(profile_exists)

        # Verify profile data
        profile = EmployeeProfile.objects(user=user).first()
        self.assertEqual(profile.first_name, self.user_data["first_name"])
        self.assertEqual(profile.last_name, self.user_data["last_name"])
        self.assertEqual(profile.department, self.user_data["department"])
        self.assertEqual(profile.position, self.user_data["position"])

    def test_login(self):
        """Test login with existing user"""
        login_data = {"email": self.existing_email, "password": "existing_password123"}

        response = self.client.post(self.login_url, login_data, format="json")

        # Check the response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("refresh", response.data)
        self.assertIn("access", response.data)
        self.assertIn("user", response.data)

        # Verify user data in response
        self.assertEqual(response.data["user"]["id"], str(self.test_user.id))

    def test_access_protected_endpoint(self):
        """Test accessing a protected endpoint with JWT token"""
        # First login to get tokens
        login_data = {"email": self.existing_email, "password": "existing_password123"}

        login_response = self.client.post(self.login_url, login_data, format="json")
        access_token = login_response.data["access"]

        # Set the authorization header
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

        # Access protected endpoint
        response = self.client.get(self.user_url)

        # Check the response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], str(self.test_user.id))

    def test_token_refresh(self):
        """Test refreshing tokens"""
        # First login to get tokens
        login_data = {"email": self.existing_email, "password": "existing_password123"}

        login_response = self.client.post(self.login_url, login_data, format="json")
        refresh_token = login_response.data["refresh"]

        # Refresh token
        refresh_data = {"refresh": refresh_token}

        response = self.client.post(self.refresh_url, refresh_data, format="json")

        # Check the response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("refresh", response.data)
        self.assertIn("access", response.data)

    def test_logout_and_token_blacklisting(self):
        """Test logout and token blacklisting"""
        # First login to get tokens
        login_data = {"email": self.existing_email, "password": "existing_password123"}

        login_response = self.client.post(self.login_url, login_data, format="json")
        refresh_token = login_response.data["refresh"]
        access_token = login_response.data["access"]

        # Decode token to get the jti
        decoded_token = jwt.decode(refresh_token, options={"verify_signature": False})
        token_jti = decoded_token["jti"]

        # Set the authorization header
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

        # Logout
        logout_data = {"refresh": refresh_token, "access": access_token}

        response = self.client.post(self.logout_url, logout_data, format="json")

        # Check the response
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check that token is blacklisted
        token_is_blacklisted = BlacklistedToken.objects.filter(
            token_jti=token_jti
        ).exists()
        self.assertTrue(token_is_blacklisted)

        # Try to use blacklisted token
        response = self.client.get(self.user_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_expired_token_cleanup(self):
        """Test cleanup of expired blacklisted tokens"""
        # Create an expired token in the blacklist
        yesterday = timezone.now() - timedelta(days=1)

        # Clean up previous test tokens if they exist
        BlacklistedToken.objects.filter(token_jti="expired_test_token").delete()
        BlacklistedToken.objects.filter(token_jti="valid_test_token").delete()

        BlacklistedToken.objects.create(
            token_jti="expired_test_token",
            user_id=str(self.test_user.id),
            blacklisted_at=yesterday,
            expires_at=yesterday,
        )

        # Create a non-expired token in the blacklist
        tomorrow = timezone.now() + timedelta(days=1)

        BlacklistedToken.objects.create(
            token_jti="valid_test_token",
            user_id=str(self.test_user.id),
            blacklisted_at=timezone.now(),
            expires_at=tomorrow,
        )

        # Verify both tokens are in the blacklist
        self.assertEqual(
            BlacklistedToken.objects.filter(
                token_jti__in=["expired_test_token", "valid_test_token"]
            ).count(),
            2,
        )

        # Run cleanup
        BlacklistedToken.clean_expired_tokens()

        # Verify only non-expired token remains
        self.assertEqual(
            BlacklistedToken.objects.filter(token_jti="valid_test_token").count(), 1
        )
        self.assertTrue(
            BlacklistedToken.objects.filter(token_jti="valid_test_token").exists()
        )
        self.assertFalse(
            BlacklistedToken.objects.filter(token_jti="expired_test_token").exists()
        )

    def tearDown(self):
        """Clean up after tests"""
        # Delete the test user and profile
        if hasattr(self, "test_user"):
            # Delete profile first
            EmployeeProfile.objects(user=self.test_user).delete()
            # Then delete user
            self.test_user.delete()

        # Clean up test tokens
        BlacklistedToken.objects.filter(
            token_jti__in=["expired_test_token", "valid_test_token"]
        ).delete()


class BlacklistedTokenModelTests(TestCase):
    """Test BlacklistedToken model functionality"""

    def setUp(self):
        """Set up test data"""
        # Clean up any existing test tokens
        BlacklistedToken.objects.filter(
            token_jti__in=[
                "test_token_jti",
                "non_existent_token",
                "expired_token",
                "valid_token",
            ]
        ).delete()

    def test_is_blacklisted(self):
        """Test checking if a token is blacklisted"""
        # Create a blacklisted token
        BlacklistedToken.objects.create(
            token_jti="test_token_jti",
            user_id="test_user_id",
            blacklisted_at=timezone.now(),
            expires_at=timezone.now() + timedelta(days=1),
        )

        # Check if token is blacklisted
        self.assertTrue(BlacklistedToken.is_blacklisted("test_token_jti"))
        self.assertFalse(BlacklistedToken.is_blacklisted("non_existent_token"))

    def test_clean_expired_tokens(self):
        """Test cleaning expired tokens"""
        # Create expired and non-expired tokens
        BlacklistedToken.objects.create(
            token_jti="expired_token", expires_at=timezone.now() - timedelta(minutes=5)
        )

        BlacklistedToken.objects.create(
            token_jti="valid_token", expires_at=timezone.now() + timedelta(minutes=5)
        )

        # Clean expired tokens
        BlacklistedToken.clean_expired_tokens()

        # Verify only valid token remains
        self.assertEqual(
            BlacklistedToken.objects.filter(
                token_jti__in=["expired_token", "valid_token"]
            ).count(),
            1,
        )
        self.assertTrue(
            BlacklistedToken.objects.filter(token_jti="valid_token").exists()
        )
        self.assertFalse(
            BlacklistedToken.objects.filter(token_jti="expired_token").exists()
        )

    def tearDown(self):
        """Clean up after tests"""
        # Clean up test tokens
        BlacklistedToken.objects.filter(
            token_jti__in=[
                "test_token_jti",
                "non_existent_token",
                "expired_token",
                "valid_token",
            ]
        ).delete()
