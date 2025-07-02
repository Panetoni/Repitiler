from django.contrib import admin # type: ignore
from .models import ReptilerUser, Video
from .inlines import VideoInline
from django.utils.html import format_html # type: ignore
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin # type: ignore
from django.contrib.auth.models import User # type: ignore
from django.contrib import admin # type: ignore
from .forms import ReptilerUserAdminForm

admin.site.unregister(User)

@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    def changelist_view(self, request, extra_context=None):
        # Usado apenas na página de listagem
        self.list_filter_original = self.list_filter
        self.list_filter = ()
        return super().changelist_view(request, extra_context)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Verifica se a view atual é a de listagem (usando URL)
        if request.resolver_match and request.resolver_match.url_name == 'auth_user_changelist':
            return qs.exclude(pk__in=ReptilerUser.objects.values_list('user_id', flat=True))
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