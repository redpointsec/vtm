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
        auth_header = request.META.get("HTTP_COOKIE", None)
        if auth_header:
            try:
                tokens = auth_header.split("; ")
                for i in tokens:
                    if "access_token" in i:
                        token = i.split("access_token=")[1]
                        break
                     # Expect "Bearer <token>"
                validated_token = AccessToken(token)
                user_id = validated_token["user_id"]
                user = User.objects.get(id=user_id)
                request.user = user
            except (IndexError, InvalidToken, TokenError, User.DoesNotExist):
                request.user = AnonymousUser()  # Set to AnonymousUser if token is invalid
        else:
            request.user = AnonymousUser()  # Default to AnonymousUser if no token provided
