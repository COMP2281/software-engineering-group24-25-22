"""
Custom authentication backend for MongoEngine User model
"""
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import AnonymousUser
from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.authentication import get_authorization_header
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed, TokenError
from rest_framework import HTTP_HEADER_ENCODING

from .models import User, BlacklistedToken


class MongoEngineBackend(BaseBackend):
    """
    Authentication backend for MongoEngine User model
    """
    
    def authenticate(self, request, email=None, password=None, **kwargs):
        """
        Authenticate a user with email and password.
        """
        if email is None:
            email = kwargs.get('username', '')
        
        try:
            # Use mongoengine's query syntax
            user = User.objects.get(email=email.lower())
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            # Run the default password hasher to reduce timing attacks
            User().check_password(password)
            return None
    
    def get_user(self, user_id):
        """
        Get a User object by ID.
        """
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None
    
    def has_perm(self, user, perm, obj=None):
        """
        Check if user has permissions
        """
        if not user.is_active:
            return False
        
        if user.is_superuser:
            return True
            
        # Implement more detailed permission checking if needed
        return False


class MongoJWTAuthentication(JWTAuthentication):
    """
    Custom JWT authentication for MongoEngine. This overrides the default
    JWT authentication to use MongoEngine instead of Django ORM.
    """
    user_id_claim = 'user_id'
    
    def get_validated_token(self, raw_token):
        """
        Override to check if the token is blacklisted
        """
        # First validate the token
        validated_token = super().get_validated_token(raw_token)
        
        # Check if token is blacklisted
        jti = validated_token.get('jti')
        if jti and BlacklistedToken.is_blacklisted(jti):
            raise InvalidToken('Token is blacklisted', code='token_blacklisted')
            
        return validated_token
    
    def get_user(self, validated_token):
        """
        Returns a MongoEngine User model instance based on the given validated token.
        """
        try:
            user_id = validated_token[self.user_id_claim]
        except KeyError:
            raise InvalidToken('Token contained no recognizable user identification')
        
        try:
            # Use MongoEngine's syntax to get the user
            user = User.objects(id=user_id).first()
            if user is None:
                raise AuthenticationFailed('User not found', code='user_not_found')
        except Exception as e:
            raise AuthenticationFailed(f'Error finding user: {str(e)}')
        
        if not user.is_active:
            raise AuthenticationFailed('User is inactive', code='user_inactive')
        
        return user