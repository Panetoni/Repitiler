# reptilerUser/signals.py

from allauth.account.signals import user_signed_up # type: ignore
from django.dispatch import receiver # type: ignore
from .models import ReptilerUser

@receiver(user_signed_up)
def create_reptiler_user(sender, request, user, **kwargs):
    # Cria o ReptilerUser automaticamente
    if not hasattr(user, 'reptiler_user'):
        ReptilerUser.objects.create(user=user)
