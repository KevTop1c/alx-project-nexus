import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Profile

logger = logging.getLogger(__name__)
User = get_user_model()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Automatically create a Profile when a new User is created.
    Uses get_or_create to handle race conditions and prevent duplicates.
    """
    if created and not kwargs.get("raw", False):  # Skip for fixture loading
        try:
            profile, created = Profile.objects.get_or_create(user=instance)
            if created:
                logger.info("Profile created for user: %s", instance.username)
        except Exception as e:
            logger.error("Failed to create profile for user %s: %s", instance.username, e)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Save the user's profile when the user is saved.
    Includes protection against infinite loops.
    """
    if kwargs.get("raw", False):  # Skip during fixture loading
        return

    try:
        if hasattr(instance, "profile"):
            # Save without triggering signals recursively
            Profile.objects.filter(pk=instance.profile.pk).update(
                updated_at=instance.profile.updated_at
            )
            logger.debug("Profile updated for user: %s", instance.username)
    except Exception as e:
        logger.error("Failed to update profile for user %s: %s", instance.username, e)
