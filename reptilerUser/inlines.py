from django.contrib import admin # type: ignore
from .models import Video
from django.utils.html import format_html # type: ignore
from django.urls import reverse # type: ignore
from .forms import VideoForm

class VideoInline(admin.TabularInline):
    model = Video
    form = VideoForm      
    extra = 0
    readonly_fields = ('video_link', 'uploaded_at',)
    fields = ('title','video_link', 'uploaded_at', 'video_file')  
    can_delete = True

    def video_link(self, obj):
        if obj.pk:
            url = reverse('admin:reptilerUser_video_change', args=[obj.pk])  
            return format_html('<a href="{}">{}</a>', url, obj.title)
        return "-"

    video_link.short_description = "Vídeo"