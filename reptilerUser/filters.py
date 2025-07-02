from django.contrib import admin # type: ignore
from allauth.socialaccount.models import SocialAccount # type: ignore
from .models import ReptilerUser 

class SpecialUsersFilter(admin.SimpleListFilter):
    title = 'Mostrar usuários especiais'
    parameter_name = 'show_special'

    def lookups(self, request, model_admin):
        return (
            ('no', 'Ocultar usuários Reptiler e Google'),
            ('yes', 'Mostrar usuários Reptiler e Google'),
        )

    def queryset(self, request, queryset):
        reptiler_ids = ReptilerUser.objects.values_list('user_id', flat=True)
        google_ids = SocialAccount.objects.filter(provider='google').values_list('user_id', flat=True)
        special_ids = list(set(reptiler_ids) | set(google_ids))

        if self.value() == 'yes':
            # Mostrar todos, incluindo especiais
            return queryset
        else:
            # Default: ocultar especiais
            return queryset.exclude(pk__in=special_ids)