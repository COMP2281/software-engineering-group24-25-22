from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from apps.accounts.models import EmployeeProfile, ExpenseSettings
from django.contrib.auth import authenticate

from .serializers import UserRegistrationSerializer, UserDetailsSerializer, EmployeeProfile, EmployeeProfileSerializer, ExpenseSettingsSerializer

# TODO: Improve the error responses

class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """
        Authenticate user and return JWT tokens
        Expected payload: {
            "email": "user@example.com",
            "password": "userpassword"
        }
        """
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return Response(
                {'error': 'Please provide both email and password'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = authenticate(email=email, password=password)
        
        if user:
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': {
                    'email': user.email,
                    'is_staff': user.is_staff,
                }
            })
        
        return Response(
            {'error': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED
        )

class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as _:
            return Response(status=status.HTTP_400_BAD_REQUEST)

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
                status=status.HTTP_404_NOT_FOUND
            )
    
    def put(self, request):
        """Update the employee profile for the authenticated user"""
        try:
            profile = EmployeeProfile.objects.get(user=request.user)
            serializer = EmployeeProfileSerializer(profile, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except EmployeeProfile.DoesNotExist:
            return Response(
                {"detail": "Employee profile not found"}, 
                status=status.HTTP_404_NOT_FOUND
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
                status=status.HTTP_404_NOT_FOUND
            )
    
    def put(self, request):
        """Update the expense settings for the authenticated user"""
        try:
            settings = ExpenseSettings.objects.get(user=request.user)
            serializer = ExpenseSettingsSerializer(settings, data=request.data, partial=True)
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
