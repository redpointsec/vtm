from django.contrib.auth.models import User, AnonymousUser
from django.utils.deprecation import MiddlewareMixin
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken


class JWTAuthenticationMiddleware(MiddlewareMixin):
    def process_request(self, request):
        token = request.COOKIES.get("access_token")
        if not token:
            return

        try:
            validated_token = AccessToken(token)
            user_id = validated_token["user_id"]
            request.user = User.objects.get(id=user_id)
        except (IndexError, InvalidToken, TokenError, User.DoesNotExist):
            request.user = AnonymousUser()
