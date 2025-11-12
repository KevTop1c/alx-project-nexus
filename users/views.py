import logging
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .serializers import (
    UserRegistrationSerializer,
    UserSerializer,
    UserProfileSerializer,
)

logger = logging.getLogger(__name__)


class RegisterView(generics.CreateAPIView):
    """
    Register a new user account
    """

    permission_classes = [AllowAny]
    serializer_class = UserRegistrationSerializer

    def create(self, request, *args, **kwargs):
        logger.info("API REQUEST: /api/users/register/ | data=%s", request.data)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)

        logger.info(
            "API RESPONSE: /api/users/register/ | status=201 | user=%s", user.username
        )

        return Response(
            {
                "user": UserSerializer(user).data,
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
            },
            status=status.HTTP_201_CREATED,
        )


@swagger_auto_schema(
    method="post",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=["username", "password"],
        properties={
            "username": openapi.Schema(type=openapi.TYPE_STRING),
            "password": openapi.Schema(type=openapi.TYPE_STRING, format="password"),
        },
    ),
    responses={
        200: openapi.Response(
            "Login successful",
            openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "user": openapi.Schema(type=openapi.TYPE_OBJECT),
                    "tokens": openapi.Schema(type=openapi.TYPE_OBJECT),
                },
            ),
        )
    },
)
@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    """
    Login with username and password to receive JWT tokens
    """
    username = request.data.get("username")
    password = request.data.get("password")

    logger.info("API REQUEST: /api/users/login/ | username=%s", username)

    if not username or not password:
        logger.warning("API WARNING: /api/users/login/ | missing credentials")
        return Response(
            {"error": "Username and password are required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = authenticate(username=username, password=password)

    if user is None:
        logger.warning(
            "API WARNING: /api/users/login/ | invalid credentials | username=%s",
            username,
        )
        return Response(
            {"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED
        )

    refresh = RefreshToken.for_user(user)

    logger.info("API RESPONSE: /api/users/login/ | status=200 | user=%s", user.username)

    return Response(
        {
            "user": UserSerializer(user).data,
            "tokens": {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            },
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def profile_view(request):
    """
    Get current user profile
    """
    logger.info("API REQUEST: /api/users/profile/ | user=%s", request.user.username)

    serializer = UserProfileSerializer(request.user.profile)

    logger.info(
        "API RESPONSE: /api/users/profile/ | status=200 | user=%s",
        request.user.username,
    )

    return Response(serializer.data)
