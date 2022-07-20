from background_task import background
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View

from core.settings.common import EMAIL_HOST_USER, BASE_URL
from .auth_helper import get_sign_in_flow, get_token_from_code, store_user, remove_user_and_token, \
    get_token_on_behalf_of
from .forms import LoginForm, CreateUserForm
# Create your views here.
from .graph_api.base import GraphAPI

DEFAULT_PASSWORD = "Ticket123!"


# Create your views here.
def login_view(request):
    form = LoginForm(request.POST or None)

    msg = None

    if request.method == "POST":

        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(username=username, password=password)
            if user is not None:
                if not user.last_login and not settings.DEBUG:
                    login(request, user)
                    return redirect("/change_password/")
                else:
                    login(request, user)
                    return redirect("/")
            else:
                msg = 'Falscher Benutzername oder falsches Passwort'
        else:
            msg = 'Error validating the form'

    return render(request, "accounts/login.html", {"form": form, "msg": msg})


def sign_in(request):
    # Get the sign-in flow
    flow = get_sign_in_flow()
    # Save the expected flow so we can use it in the callback
    request.session['auth_flow'] = flow
    # Redirect to the Azure sign-in page
    return HttpResponseRedirect(flow['auth_uri'])


def callback(request):
    try:
        json_token = request.GET.get("jwt")
        email = request.GET.get("email")

        if json_token:
            get_token_on_behalf_of(request, json_token)
            user = GraphAPI().get_profile_as_app(email=email)
        else:
            get_token_from_code(request)
            user = GraphAPI(request=request).get_profile()

        store_user(request, user)

    except ValueError as E:
        print(E)

    return HttpResponseRedirect(reverse('home'))


def sign_out(request):
    logout(request)
    remove_user_and_token(request)

    return HttpResponseRedirect(reverse('home'))


class ChangePasswordView(View):
    def get(self, request):
        form = PasswordChangeForm(request.user)
        context = {"form": form}
        return render(request, "accounts/change_password.html", context)

    def post(self, request):
        new_password1 = request.POST.get("new_password1")
        new_password2 = request.POST.get("new_password2")
        user = request.user
        if new_password1 == new_password2:
            user.set_password(new_password1)
            user.save()
            login(request, user)
            return redirect("/")
        else:
            form = PasswordChangeForm(request.user)
            msg = "Uups! Die eingegebene Passwörter sind nicht gleich.  Nochmal versuchen."
            return render(request, "accounts/change_password.html", {"form": form, "msg": msg})


@background(schedule=1)
def send_password_reset_email(send_to):
    print(f"Sending PW reset email to: {send_to}")
    return send_mail(
        subject="TinyTeamsTicket: Dein Passwort wurde zurückgesetzt",
        message=f"""
        Dein Passwort wurde zurückgesetzt.  Du kannst auf {BASE_URL} mit den folgenden Zugangsdaten einloggen und dein Passwort ändern:
        - {send_to[0]}
        - {DEFAULT_PASSWORD}

        Bitte nicht auf diese Email antworten.

        Beste Grüße,
        IT
        """,
        from_email=EMAIL_HOST_USER,
        recipient_list=send_to,
        fail_silently=True
    )


@background(schedule=1)
def send_user_created_email_notification(send_to):
    print(f"Sending PW reset email to: {send_to}")
    return send_mail(
        subject="Ticket: Dein Konto wurde angelegt",
        message=f"""
        Ein Konto wurde für dich angelegt.  Du kannst auf {BASE_URL} mit den folgenden Zugangsdaten einloggen und dein Passwort ändern:
        - {send_to[0]}
        - {DEFAULT_PASSWORD}

        Bitte nicht auf diese Email antworten.

        Beste Grüße,
        IT
        """,
        from_email="x@y.com",
        recipient_list=send_to,
        fail_silently=True
    )


class ResetPasswordView(View):
    def post(self, request, id):
        if request.user.is_staff:
            user = User.objects.get(id=id)
            user.last_login = None
            user.set_password(DEFAULT_PASSWORD)
            user.save()
            send_password_reset_email([user.email])
            return JsonResponse({"data": "success"})


class CreateUserView(View):
    def get(self, request):
        form = CreateUserForm()
        return render(request, 'create_user.html', {"form": form})

    def post(self, request):
        name = request.POST.get('name')
        email = request.POST.get('email')
        new_user = User(
            first_name=name,
            email=email,
            username=email
        )
        new_user.set_password(DEFAULT_PASSWORD)
        new_user.save()
        send_user_created_email_notification([email])
        return JsonResponse({"name": name, "email": email})
