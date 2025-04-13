from django.urls import path
from .views import (
    RegisterView,
    LoginView,
    LogoutView,
    UserDetailView,
    EmployeeProfileView,
    ExpenseSettingsView,
    CustomTokenRefreshView,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),  # Custom login view
    # path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),  # JWT token view
    path("refresh/", CustomTokenRefreshView.as_view(), name="token_refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("user/", UserDetailView.as_view(), name="user_details"),
    path("profile/", EmployeeProfileView.as_view(), name="employee_profile"),
    path("expense-settings/", ExpenseSettingsView.as_view(), name="expense_settings"),
]
