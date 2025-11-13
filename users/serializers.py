from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from .models import UserProfile


class UserSerializer(serializers.ModelSerializer):
    """Serializes core User model data for safe read operations."""

    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name"]
        read_only_fields = ["id"]


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Handles user registration with password validation and profile creation."""

    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
            "password_confirm",
            "first_name",
            "last_name",
        ]

    def validate(self, data):
        if data["password"] != data["password_confirm"]:
            raise serializers.ValidationError("Passwords do not match")
        return data

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        user = User.objects.create_user(**validated_data)
        UserProfile.objects.create(user=user)
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializes UserProfile with nested user data."""

    user = UserSerializer(read_only=True)

    class Meta:
        model = UserProfile
        fields = ["user", "bio", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Simple token serializer that handles login and adds user data to response
    """

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = {
            "id": self.user.id,
            "username": self.user.username,
            "email": self.user.email,
            "first_name": self.user.first_name,
            "last_name": self.user.last_name,
        }
        return data
