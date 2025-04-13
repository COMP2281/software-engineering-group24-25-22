from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .models import EmployeeProfile, ExpenseSettings, BlacklistedToken
import mongoengine.errors
import jwt
from datetime import datetime

from .serializers import (
    UserRegistrationSerializer,
    UserDetailsSerializer,
    EmployeeProfileSerializer,
    ExpenseSettingsSerializer,
    CustomTokenObtainPairSerializer,
    CustomTokenRefreshSerializer,
)

# TODO: Improve the error responses


class RegisterView(APIView):
    """
    Register User and return JWT Tokens
    Expected payload: {
        "email": "user@example.com",
        "password": "userpassword"
        "password2": "userpassword",
        "first_name": "Test",
        "last_name": "User",
        "department": "Engineering",
        "position": "Developer"
    }
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        # First validate the registration data
        serializer = UserRegistrationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            # At this point data is valid - if user is authenticated, blacklist their token
            # before creating the new account
            if request.user and request.user.is_authenticated:
                try:
                    # Get the current token from auth header
                    auth_header = request.META.get("HTTP_AUTHORIZATION", "")
                    if auth_header.startswith("Bearer "):
                        token = auth_header.split(" ")[1]
                        # Decode the token without verifying signature
                        decoded_token = jwt.decode(
                            token, options={"verify_signature": False}
                        )

                        # Get token details
                        jti = decoded_token.get("jti")
                        exp = decoded_token.get("exp")
                        user_id = decoded_token.get("user_id")

                        if jti and exp and user_id:
                            # Blacklist the current token
                            BlacklistedToken.objects.create(
                                token_jti=jti,
                                user_id=user_id,
                                expires_at=datetime.fromtimestamp(exp),
                            )
                except Exception as e:
                    # Log the error but continue with registration
                    print(f"Error blacklisting token: {str(e)}")

            # Proceed with user creation
            user = serializer.save()
            refresh = RefreshToken.for_user(user)

            # Get the user's profile
            profile = EmployeeProfile.objects(user=user).first()
            profile_data = EmployeeProfileSerializer(profile).data if profile else None

            # Include user details with profile in the response
            user_data = UserDetailsSerializer(user).data
            user_data["profile"] = profile_data

            return Response(
                {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                    "user": user_data,
                },
                status=status.HTTP_201_CREATED,
            )
        except mongoengine.errors.NotUniqueError:
            return Response(
                {"email": ["A user with this email already exists."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class LoginView(TokenObtainPairView):
    """Custom JWT token view for MongoEngine User model"""

    serializer_class = CustomTokenObtainPairSerializer


class CustomTokenRefreshView(TokenRefreshView):
    """Custom token refresh view for MongoEngine User model"""

    serializer_class = CustomTokenRefreshSerializer


# Removed Custom Login View and and renamed the CustomTokenObtainPairView to LoginView.


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response(
                    {"error": "Refresh token is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Decode the token to get its claims
            decoded_token = jwt.decode(
                refresh_token,
                options={
                    "verify_signature": False
                },  # We don't need to verify the signature here
            )

            # Get the token ID and expiration
            jti = decoded_token.get("jti")
            exp = decoded_token.get("exp")
            user_id = decoded_token.get("user_id")

            if not jti or not exp:
                return Response(
                    {"error": "Invalid token format"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Add to blacklist
            BlacklistedToken.objects.create(
                token_jti=jti, user_id=user_id, expires_at=datetime.fromtimestamp(exp)
            )

            # Also blacklist the access token if provided
            access_token = request.data.get("access")
            if access_token:
                try:
                    decoded_access = jwt.decode(
                        access_token, options={"verify_signature": False}
                    )

                    access_jti = decoded_access.get("jti")
                    access_exp = decoded_access.get("exp")

                    if access_jti and access_exp:
                        BlacklistedToken.objects.create(
                            token_jti=access_jti,
                            user_id=user_id,
                            expires_at=datetime.fromtimestamp(access_exp),
                        )
                except Exception:
                    # Ignore access token blacklisting errors
                    pass

            # Clean up any expired tokens
            BlacklistedToken.clean_expired_tokens()

            return Response(
                {"detail": "Successfully logged out"}, status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": f"Unable to log out: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class UserDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserDetailsSerializer(request.user)
        return Response(serializer.data)


class EmployeeProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Get the employee profile for the authenticated user"""
        try:
            profile = EmployeeProfile.objects.get(user=request.user)
            serializer = EmployeeProfileSerializer(profile)
            return Response(serializer.data)
        except EmployeeProfile.DoesNotExist:
            return Response(
                {"detail": "Employee profile not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

    # Removed it, still considering.
    # def post(self, request):
    #     """Create a new employee profile for the authenticated user"""
    #     try:
    #         # Check if profile already exists
    #         profile = EmployeeProfile.objects(user=request.user).first()
    #         if profile:
    #             return Response(
    #                 {"detail": "Employee profile already exists"},
    #                 status=status.HTTP_400_BAD_REQUEST
    #             )
    #
    #         # Create new profile
    #         data = request.data.copy()
    #         data['user'] = str(request.user.id)
    #
    #         serializer = EmployeeProfileSerializer(data=data)
    #         if serializer.is_valid():
    #             profile = serializer.save()
    #             return Response(serializer.data, status=status.HTTP_201_CREATED)
    #         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    #     except Exception as e:
    #         return Response(
    #             {"detail": f"Error creating profile: {str(e)}"},
    #             status=status.HTTP_500_INTERNAL_SERVER_ERROR
    #         )

    def put(self, request):
        """Update the employee profile for the authenticated user"""
        try:
            # Keep the .get() method as it's correct in MongoEngine too
            profile = EmployeeProfile.objects.get(user=request.user)
            print(f"Found profile: {profile}")
            print(f"Request data: {request.data}")

            # Add user ID to the data - this is required by the serializer
            data = request.data.copy()
            data["user"] = str(request.user.id)

            serializer = EmployeeProfileSerializer(profile, data=data, partial=True)
            is_valid = serializer.is_valid()
            print(f"Is valid: {is_valid}")

            if not is_valid:
                print(f"Validation errors: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            print("Saving profile...")
            updated_profile = serializer.save()
            print(f"Updated profile: {updated_profile}")
            return Response(serializer.data)
        except EmployeeProfile.DoesNotExist:
            return Response(
                {"detail": "Employee profile not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            print(f"Error updating profile: {str(e)}")
            return Response(
                {"detail": f"Error updating profile: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ExpenseSettingsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Get the expense settings for the authenticated user"""
        try:
            settings = ExpenseSettings.objects.get(user=request.user)
            serializer = ExpenseSettingsSerializer(settings)
            return Response(serializer.data)
        except ExpenseSettings.DoesNotExist:
            return Response(
                {"detail": "Expense settings not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

    def put(self, request):
        """Update the expense settings for the authenticated user"""
        try:
            settings = ExpenseSettings.objects.get(user=request.user)
            serializer = ExpenseSettingsSerializer(
                settings, data=request.data, partial=True
            )
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ExpenseSettings.DoesNotExist:
            # Create settings if they don't exist
            serializer = ExpenseSettingsSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(user=request.user)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
