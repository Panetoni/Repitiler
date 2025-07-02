from django.contrib import admin # type: ignore
from .models import ReptilerUser, Video
from .inlines import VideoInline
from django.utils.html import format_html # type: ignore
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin # type: ignore
from django.contrib.auth.models import User # type: ignore
from django.contrib import admin # type: ignore
from .forms import ReptilerUserAdminForm
from allauth.socialaccount.models import SocialAccount # type: ignore
from .filters import SpecialUsersFilter

admin.site.unregister(User)
# Custom User Admin que não mostra os usuários especiais. Foi feito um filtro para ele que permite ver todos os user registrados. 
# Isso foi feito para que o admin não fique poluído com usuários que não são administradores do sistema, como os usuários do Google e os custom users Repitiler.
@admin.register(User)
class CustomUserAdmin(BaseUserAdmin): 
    list_filter = (SpecialUsersFilter,)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.resolver_match and request.resolver_match.url_name == 'auth_user_changelist':
            if request.GET.get('show_special') != 'yes':
                reptiler_ids = ReptilerUser.objects.values_list('user_id', flat=True)
                google_ids = SocialAccount.objects.filter(provider='google').values_list('user_id', flat=True)
                special_ids = list(set(reptiler_ids) | set(google_ids))
                qs = qs.exclude(pk__in=special_ids)
        return qs




@admin.register(ReptilerUser)
class ReptilerUserAdmin(admin.ModelAdmin):
    form = ReptilerUserAdminForm
    list_display = ('user', 'name_public', 'email')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')
    inlines = [VideoInline]

    fieldsets = (
        (None, {
            'fields': ('user', 'name_public', 'email')
        }),
    )

    def name_public(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip()

    def email(self, obj):
        return obj.user.email


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'reptiler_user', 'uploaded_at')
    readonly_fields = ('video_player',)
    fields = ('title', 'description', 'reptiler_user', 'video_file', 'video_player')

    def video_player(self, obj):
        if obj.video_file and obj.video_file.url:
            return format_html(
                '<video width="640" height="360" controls>'
                '<source src="{}" type="video/mp4">'
                'Seu navegador não suporta vídeo.'
                '</video>',
                obj.video_file.url
            )
        return "Nenhum vídeo disponível"
    
    video_player.short_description = "Reprodução do vídeo"