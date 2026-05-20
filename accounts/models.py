from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class CustomerProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="customer_profile"
    )

    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=80, default="Delhi", blank=True)
    pincode = models.CharField(max_length=10, blank=True)
    landmark = models.CharField(max_length=150, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Customer Profile"
        verbose_name_plural = "Customer Profiles"
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.user.username} Profile"

    def full_address(self):
        parts = []

        if self.address:
            parts.append(self.address)

        if self.landmark:
            parts.append(f"Landmark: {self.landmark}")

        if self.city:
            parts.append(self.city)

        if self.pincode:
            parts.append(f"PIN: {self.pincode}")

        return ", ".join(parts)


@receiver(post_save, sender=User)
def create_or_update_customer_profile(sender, instance, created, **kwargs):
    if instance.is_superuser:
        return

    if created:
        CustomerProfile.objects.create(user=instance)
    else:
        CustomerProfile.objects.get_or_create(user=instance)
