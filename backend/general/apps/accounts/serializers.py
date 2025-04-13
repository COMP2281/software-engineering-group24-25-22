from rest_framework import serializers
from common.serializers import DocumentSerializer
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import User, EmployeeProfile, ExpenseSettings, BlacklistedToken
from datetime import datetime
import jwt


# Base serializer for MongoEngine documents
class UserRegistrationSerializer(DocumentSerializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )
    password2 = serializers.CharField(write_only=True, required=True)

    # Employee profile fields
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    department = serializers.CharField(required=True)
    position = serializers.CharField(required=True)
    manager = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    class Meta:
        model = User
        fields = (
            "email",
            "password",
            "password2",
            "first_name",
            "last_name",
            "department",
            "position",
            "manager",
        )

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError(
                {"password": "Password fields didn't match."}
            )
        # Validate manager if provided
        manager = attrs.get("manager")
        if manager and manager.strip():
            try:
                # Check if manager exists
                manager_profile = EmployeeProfile.objects(id=manager).first()
                if not manager_profile:
                    raise serializers.ValidationError({"manager": "Manager not found"})
            except Exception:
                raise serializers.ValidationError({"manager": "Invalid manager ID"})

        return attrs

    def create(self, validated_data):
        # Extract profile data
        profile_data = {
            "first_name": validated_data.pop("first_name"),
            "last_name": validated_data.pop("last_name"),
            "department": validated_data.pop("department"),
            "position": validated_data.pop("position"),
        }

        # Get optional manager
        manager_id = validated_data.pop("manager", None)
        if manager_id and manager_id.strip():
            profile_data["manager"] = EmployeeProfile.objects.get(id=manager_id)

        # Remove the password confirmation field
        validated_data.pop("password2")

        # Create user
        user = User.create_user(**validated_data)

        # Generate employee ID based on total count + 1
        employee_count = EmployeeProfile.objects.count()
        employee_id = str(employee_count + 1)

        # Create employee profile
        profile_data["employee_id"] = employee_id
        profile_data["user"] = user

        profile = EmployeeProfile(**profile_data)
        profile.save()

        return user


class UserProfileSerializer(DocumentSerializer):
    id = serializers.CharField(read_only=True)

    class Meta:
        model = EmployeeProfile
        fields = (
            "id",
            "employee_id",
            "first_name",
            "last_name",
            "department",
            "position",
        )


class UserDetailsSerializer(DocumentSerializer):
    id = serializers.CharField(read_only=True)
    profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "email", "profile", "is_staff", "date_joined", "last_login")
        read_only_fields = ("email", "is_staff", "date_joined", "last_login")

    def get_profile(self, obj):
        try:
            profile = EmployeeProfile.objects(user=obj).first()
            return EmployeeProfileSerializer(profile).data if profile else None
        except Exception:
            return None


class EmployeeProfileSerializer(DocumentSerializer):
    id = serializers.CharField(read_only=True)
    user = serializers.CharField()
    manager = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    # Add explicit fields for all profile attributes
    employee_id = serializers.CharField(read_only=True)
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    department = serializers.CharField(required=False)
    position = serializers.CharField(required=False)

    class Meta:
        model = EmployeeProfile
        fields = (
            "id",
            "user",
            "employee_id",
            "first_name",
            "last_name",
            "department",
            "position",
            "manager",
        )
        read_only_fields = ("employee_id",)  # Typically not changed after creation

    def validate_user(self, value):
        try:
            return User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid user ID")

    def validate_manager(self, value):
        if not value or value == "":
            return None

        try:
            return EmployeeProfile.objects.get(id=value)
        except EmployeeProfile.DoesNotExist:
            raise serializers.ValidationError("Invalid manager ID")


class ExpenseSettingsSerializer(DocumentSerializer):
    id = serializers.CharField(read_only=True)
    user = serializers.CharField()
    expense_approver = serializers.CharField(required=False, allow_null=True)

    class Meta:
        model = ExpenseSettings
        fields = (
            "id",
            "user",
            "default_currency",
            "expense_approver",
            "monthly_expense_limit",
        )

    def validate_user(self, value):
        try:
            return User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid user ID")

    def validate_expense_approver(self, value):
        if not value:
            return None

        try:
            return User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid approver ID")


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom JWT token serializer for MongoEngine User model"""

    username_field = "email"

    @classmethod
    def get_token(cls, user):
        """Add custom claims to the token"""
        token = super().get_token(user)

        # Add custom claims
        token["email"] = user.email
        token["is_staff"] = user.is_staff

        return token

    def validate(self, attrs):
        """Authenticate user and return tokens"""
        from django.contrib.auth import authenticate

        # Set default values for username/password fields
        self.fields["email"] = serializers.CharField()
        self.fields["password"] = serializers.CharField()

        # Get credentials from request
        email = attrs.get("email", "")
        password = attrs.get("password", "")

        # Authenticate user
        try:
            request = self.context.get("request", None)
            user = authenticate(request=request, email=email, password=password)

            if not user:
                raise serializers.ValidationError("Invalid email or password")

            if not user.is_active:
                raise serializers.ValidationError("User account is disabled")

            # Generate tokens
            refresh = self.get_token(user)

            return {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": UserDetailsSerializer(user).data,
            }
        except Exception as e:
            raise serializers.ValidationError(f"Unable to log in: {str(e)}")


class CustomTokenRefreshSerializer(serializers.Serializer):
    """
    Custom token refresh serializer for MongoEngine User model
    """

    refresh = serializers.CharField()

    def validate(self, attrs):
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework_simplejwt.exceptions import TokenError

        try:
            # First, check if the token is blacklisted
            decoded = jwt.decode(attrs["refresh"], options={"verify_signature": False})
            jti = decoded.get("jti")

            if jti and BlacklistedToken.is_blacklisted(jti):
                raise serializers.ValidationError("Token is blacklisted")

            # If not blacklisted, continue with refresh
            refresh = RefreshToken(attrs["refresh"])
            user_id = refresh.payload.get("user_id")

            # Verify user exists in mongoengine
            user = User.objects(id=user_id).first()
            if not user:
                raise serializers.ValidationError("User not found")

            # Get settings for token rotation
            from django.conf import settings

            # Check if we should rotate refresh tokens
            if settings.SIMPLE_JWT.get("ROTATE_REFRESH_TOKENS", False):
                # If rotation is enabled, blacklist the current token if required
                if settings.SIMPLE_JWT.get("BLACKLIST_AFTER_ROTATION", False):
                    try:
                        BlacklistedToken.objects.create(
                            token_jti=jti,
                            user_id=user_id,
                            expires_at=datetime.fromtimestamp(decoded.get("exp", 0)),
                        )
                    except Exception as e:
                        # Log the error but continue
                        print(f"Error blacklisting token: {str(e)}")

                # Create a new refresh token
                new_refresh = RefreshToken.for_user(user)

                # Preserve any custom claims from the old token
                for key, value in refresh.payload.items():
                    if key not in [
                        "exp",
                        "iat",
                        "jti",
                    ]:  # Skip standard claims that are auto-set
                        new_refresh[key] = value

                # Return new refresh and access tokens
                return {
                    "refresh": str(new_refresh),
                    "access": str(new_refresh.access_token),
                }
            else:
                # If rotation is disabled, return original refresh token
                return {"refresh": str(refresh), "access": str(refresh.access_token)}
        except TokenError as e:
            raise serializers.ValidationError(str(e))
        except Exception as e:
            raise serializers.ValidationError(f"Token refresh failed: {str(e)}")
