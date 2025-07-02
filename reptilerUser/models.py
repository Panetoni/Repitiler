from django.db import models # type: ignore
from django.db.models import CharField, IntegerField #type: ignore
from django.contrib.auth.models import User #type: ignore
from django.db import models #type: ignore
from django.contrib.auth.models import User #type: ignore


#----------------------------------- Usuário ---------------------------------------------------


class ReptilerUser(models.Model):
    """Extensão do modelo User com dados adicionais."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='reptiler_user')

    @property
    def name_public(self):
        return f"{self.user.first_name} {self.user.last_name}".strip()

    @name_public.setter
    def name_public(self, full_name):
        names = full_name.strip().split(" ", 1)
        self.user.first_name = names[0]
        self.user.last_name = names[1] if len(names) > 1 else ""
        self.user.save()

    def __str__(self):
        return self.user.username

#----------------------------------- Fim Usuário ------------------------------------------------

#----------------------------------- Vídeo ---------------------------------------------------
class Video(models.Model):
    """Modelo para armazenar vídeos."""
    
    reptiler_user = models.ForeignKey('ReptilerUser', on_delete=models.CASCADE, related_name='videos')
    """Relaciona o vídeo com um usuário do Reptiler."""
    
    title = CharField(max_length=100)
    description = CharField(max_length=500, blank=True, null=True)
    video_file = models.FileField(upload_to='videos/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
#----------------------------------- Fim Vídeo ---------------------------------------------------