from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.views import LogoutView
from django.urls import path

from .views import login_view, sign_in, callback, sign_out, ChangePasswordView, ResetPasswordView, CreateUserView

urlpatterns = [
    path('login/', login_view, name="login"),
    path('change_password/', ChangePasswordView.as_view(), name="change_password"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path('signin/', sign_in, name='signin'),
    path('callback/', callback, name='callback'),
    path('signout/', sign_out, name='signout'),
    path('create-user/', staff_member_required(CreateUserView.as_view()), name="create-user"),
    path('reset-password/<int:id>/', staff_member_required(ResetPasswordView.as_view()), name="reset-password"),
]
