import json
import traceback

import requests
import yaml
from django.conf import settings

from authentication.auth_helper import get_token

stream = open('authentication/oauth_settings.yml', 'r')
oauth_settings = yaml.load(stream, yaml.SafeLoader)


class GraphAPI:

    def __init__(self, request=None):
        # Get access token on behalf of user if request else as application
        if settings.DEBUG:
            self.token = 'faketokenfordevelopment'
        else:
            self.token = get_token(request) if request else self.get_access_token_as_application()
        self.headers = {
                'Authorization': f"Bearer {self.token}",
                'Content-Type': "application/json"
            }
        self.is_obo_application = False if request else True

    @staticmethod
    def get_access_token_as_application():
        print("GETTING ACCESS TOKEN AS APPLICATION")
        tenant = oauth_settings["tenant_id"]
        url = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"
        payload = {
            "client_id": oauth_settings["app_id"],
            "scope": "https://graph.microsoft.com/.default",
            "client_secret": oauth_settings["app_secret"],
            "grant_type": "client_credentials"
        }
        request = requests.post(url=url, data=payload)
        response = request.json()
        print("ACCESS TOKEN RESPONSE:", response)
        return response["access_token"]

    def request(self, http_verb, endpoint=None, payload=None):
        if not endpoint:
            endpoint = "/"
        try:
            url = f"https://graph.microsoft.com/v1.0{endpoint}"
            payload = json.dumps(payload) if payload else {}
            response = requests.request(http_verb, url, headers=self.headers, data=payload)

            return response.json() if response.status_code != 204 else None
        except Exception as e:
            print(traceback.format_exc())
            return e

    def refresh_token(self):
        print("REFRESHING ACCESS TOKEN")
        self.token = self.get_access_token_as_application()
        self.headers = {
                'Authorization': f"Bearer {self.token}",
                'Content-Type': "application/json"
            }

    def get_profile_as_app(self, email):
        return self.request(http_verb="GET", endpoint=f"/users/{email}")

    def get_profile(self):
        return self.request(http_verb="GET", endpoint="/me")

    def send_activity_feed_notification(self, user_id, payload):
        return self.request(http_verb="POST",
                            endpoint=f"/users/{user_id}/teamwork/sendActivityNotification",
                            payload=payload)

    def get_all_users(self):
        response = self.request(http_verb="GET", endpoint="/users")
        users = response["value"]
        next_link = response["@odata.nextLink"] if "@odata.nextLink" in response.keys() else False
        while next_link:
            request = requests.get(url=next_link, headers=self.headers)
            next_users = request.json()
            for user in next_users["value"]:
                users.append(user)
            next_link = next_users["@odata.nextLink"] if "@odata.nextLink" in next_users.keys() else False
        return users
