"""
User and authentication models for jRetireWise.
"""

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    """Extended user profile with application-specific data."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    google_oauth_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    full_name = models.CharField(max_length=255, blank=True)
    theme_preference = models.CharField(
        max_length=10,
        choices=[('light', 'Light'), ('dark', 'Dark')],
        default='light'
    )
    notification_email = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'authentication_userprofile'
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
        indexes = [
            models.Index(fields=['google_oauth_id']),
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f"Profile of {self.user.email}"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Automatically create a UserProfile when a new User is created."""
    if created:
        UserProfile.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Automatically save the UserProfile when a User is saved."""
    instance.profile.save()
