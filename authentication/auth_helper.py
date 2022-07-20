import msal
import yaml
from django.conf import settings
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.urls import reverse

from authentication.models import MicrosoftProfile

stream = open('authentication/oauth_settings.yml', 'r')
oauth_settings = yaml.load(stream, yaml.SafeLoader)


def load_cache(request):
    # Check for a token cache in the session
    cache = msal.SerializableTokenCache()
    if request.session.get('token_cache'):
        cache.deserialize(request.session['token_cache'])

    return cache


def save_cache(request, cache):
    # If cache has changed, persist back to session
    if cache.has_state_changed:
        request.session['token_cache'] = cache.serialize()


def get_msal_app(cache=None):
    # Initialize the MSAL confidential client
    auth_app = msal.ConfidentialClientApplication(
        oauth_settings['app_id'],
        authority=oauth_settings['authority'],
        client_credential=oauth_settings['app_secret'],
        token_cache=cache)

    return auth_app


# Method to generate a sign-in flow
def get_sign_in_flow():
    auth_app = get_msal_app()
    prefix = 'http://' if 'localhost' in settings.BASE_URL else ''
    redirect_uri = prefix + settings.BASE_URL + oauth_settings['redirect']
    redirect_uri = redirect_uri.replace('www.', '')

    return auth_app.initiate_auth_code_flow(
        oauth_settings['scopes'],
        redirect_uri=redirect_uri)


# Method to exchange auth code for access token
def get_token_from_code(request):
    cache = load_cache(request)
    auth_app = get_msal_app(cache)

    # Get the flow saved in session
    flow = request.session.pop('auth_flow', {})

    result = auth_app.acquire_token_by_auth_code_flow(flow, request.GET)
    save_cache(request, cache)

    return result


def get_token_on_behalf_of(request, json_token):
    cache = load_cache(request)
    auth_app = get_msal_app(cache)
    token = auth_app.acquire_token_on_behalf_of(
        user_assertion=json_token,
        scopes=oauth_settings["scopes"]
    )
    save_cache(request, cache)

    return token


def login_user(request, user):
    """
    Log in a user without requiring credentials (using ``login`` from
    ``django.contrib.auth``, first finding a matching backend).

    """
    from django.contrib.auth import load_backend, login
    if not hasattr(user, 'backend'):
        for backend in settings.AUTHENTICATION_BACKENDS:
            if user == load_backend(backend).get_user(user.pk):
                user.backend = backend
                break
    if hasattr(user, 'backend'):
        return login(request, user)
    else:
        return login(request, user, backend=settings.AUTHENTICATION_BACKENDS[0])


def store_user(request, user):
    print("LOGGING IN USER:", user)
    name = user['displayName']
    email = user['mail']
    ms_id = user['id']

    request.session['user'] = {
        'is_authenticated': True,
        'name': name,
        'email': email
    }
    dj_user, created = User.objects.update_or_create(
        username=email,
        defaults={
            "email": email
        }
    )

    if created:
        dj_user.first_name = name
        dj_user.set_password(email)
        dj_user.save()

    MicrosoftProfile.objects.update_or_create(
        user=dj_user,
        defaults={"ms_id": ms_id})
    login_user(request, dj_user)


def get_token(request):
    cache = load_cache(request)
    auth_app = get_msal_app(cache)

    accounts = auth_app.get_accounts()
    if accounts:
        result = auth_app.acquire_token_silent(
            oauth_settings['scopes'],
            account=accounts[0])

        save_cache(request, cache)

        return result['access_token']


def remove_user_and_token(request):
    if 'token_cache' in request.session:
        del request.session['token_cache']

    if 'user' in request.session:
        del request.session['user']


def sign_out(request):
    # Clear out the user and token
    remove_user_and_token(request)

    return HttpResponseRedirect(reverse('home'))


def initialize_context(request):
    context = {}

    # Check for any errors in the session
    error = request.session.pop('flash_error', None)

    if error != None:
        context['errors'] = []
        context['errors'].append(error)

    # Check for user in the session
    context['user'] = request.session.get('user', {'is_authenticated': False})
    return context
