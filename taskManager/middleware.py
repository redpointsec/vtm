# middleware.py
import jwt
from django.conf import settings
from django.contrib.auth.models import User, AnonymousUser
from django.utils.deprecation import MiddlewareMixin
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken


# middleware.py


class JWTAuthenticationMiddleware(MiddlewareMixin):
    def process_request(self, request):
        token = request.COOKIES.get("access_token")
        if token:
            try:
                validated_token = AccessToken(token)
                user_id = validated_token["user_id"]
                user = User.objects.get(id=user_id)
                request.user = user
            except (IndexError, InvalidToken, TokenError, User.DoesNotExist):
                request.user = AnonymousUser()  # Set to AnonymousUser if token is invalid
        else:
            request.user = AnonymousUser()  # Default to AnonymousUser if no token provided
