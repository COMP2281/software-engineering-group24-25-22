from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import User, EmployeeProfile, ExpenseSettings

# Base serializer for MongoEngine documents
class MongoEngineModelSerializer(serializers.Serializer):
    """Base serializer for MongoEngine documents"""
    
    def create(self, validated_data):
        """Create a new instance from validated data"""
        instance = self.Meta.model(**validated_data)
        instance.save()
        return instance
    
    def update(self, instance, validated_data):
        """Update an existing instance with validated data"""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

class UserRegistrationSerializer(MongoEngineModelSerializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = ('email', 'password', 'password2')
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.create_user(**validated_data)
        return user

class UserProfileSerializer(MongoEngineModelSerializer):
    id = serializers.CharField(read_only=True)
    
    class Meta:
        model = EmployeeProfile
        fields = ('id', 'employee_id', 'first_name', 'last_name', 'department', 'position')

class UserDetailsSerializer(MongoEngineModelSerializer):
    id = serializers.CharField(read_only=True)
    profile = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ('id', 'email', 'profile', 'is_staff', 'date_joined', 'last_login')
        read_only_fields = ('email', 'is_staff', 'date_joined', 'last_login')
    
    def get_profile(self, obj):
        try:
            profile = EmployeeProfile.objects(user=obj).first()
            return UserProfileSerializer(profile).data if profile else None
        except Exception:
            return None

class EmployeeProfileSerializer(MongoEngineModelSerializer):
    id = serializers.CharField(read_only=True)
    user = serializers.CharField()
    manager = serializers.CharField(required=False, allow_null=True)
    
    class Meta:
        model = EmployeeProfile
        fields = ('id', 'user', 'employee_id', 'first_name', 'last_name', 'department', 'position', 'manager')
        read_only_fields = ('employee_id',)  # Typically not changed after creation
    
    def validate_user(self, value):
        try:
            return User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid user ID")
    
    def validate_manager(self, value):
        if not value:
            return None
        
        try:
            return EmployeeProfile.objects.get(id=value)
        except EmployeeProfile.DoesNotExist:
            raise serializers.ValidationError("Invalid manager ID")

class ExpenseSettingsSerializer(MongoEngineModelSerializer):
    id = serializers.CharField(read_only=True)
    user = serializers.CharField()
    expense_approver = serializers.CharField(required=False, allow_null=True)
    
    class Meta:
        model = ExpenseSettings
        fields = ('id', 'user', 'default_currency', 'expense_approver', 'monthly_expense_limit')
    
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
    
    username_field = 'email'
    
    @classmethod
    def get_token(cls, user):
        """Add custom claims to the token"""
        token = super().get_token(user)
        
        # Add custom claims
        token['email'] = user.email
        token['is_staff'] = user.is_staff
        
        return token
    
    def validate(self, attrs):
        """Authenticate user and return tokens"""
        from django.contrib.auth import authenticate
        
        # Set default values for username/password fields
        self.fields['email'] = serializers.CharField()
        self.fields['password'] = serializers.CharField()
        
        # Get credentials from request
        email = attrs.get('email', '')
        password = attrs.get('password', '')
        
        # Authenticate user
        try:
            request = self.context.get('request', None)
            user = authenticate(
                request=request,
                email=email,
                password=password
            )
            
            if not user:
                raise serializers.ValidationError('Invalid email or password')
            
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled')
            
            # Generate tokens
            refresh = self.get_token(user)
            
            return {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': UserDetailsSerializer(user).data
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
            refresh = RefreshToken(attrs['refresh'])
            user_id = refresh.payload.get('user_id')
            
            # Verify user exists in mongoengine
            user = User.objects(id=user_id).first()
            if not user:
                raise serializers.ValidationError('User not found')
            
            # Return refresh and access tokens
            return {
                'refresh': str(refresh),
                'access': str(refresh.access_token)
            }
        except TokenError as e:
            raise serializers.ValidationError(str(e))
        except Exception as e:
            raise serializers.ValidationError(f"Token refresh failed: {str(e)}")
