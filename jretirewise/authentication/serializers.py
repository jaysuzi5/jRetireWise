"""
Serializers for authentication.
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    email = serializers.CharField(source='user.email', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    theme_preference = serializers.ChoiceField(choices=[('light', 'Light'), ('dark', 'Dark')])

    class Meta:
        model = UserProfile
        fields = ('email', 'username', 'full_name', 'theme_preference', 'notification_email')


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 'profile')
