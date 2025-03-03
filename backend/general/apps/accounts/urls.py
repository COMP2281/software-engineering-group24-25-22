from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import RegisterView, LogoutView, UserDetailView, EmployeeProfileView, ExpenseSettingsView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('login/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('user/', UserDetailView.as_view(), name='user_details'),
    path('profile/', EmployeeProfileView.as_view(), name='employee_profile'),
    path('expense-settings/', ExpenseSettingsView.as_view(), name='expense_settings'),
]
