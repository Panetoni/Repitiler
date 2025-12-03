from django.db import models # type: ignore
from django.db.models import CharField, IntegerField #type: ignore
from django.contrib.auth.models import User #type: ignore
from django.db import models #type: ignore
from django.contrib.auth.models import User #type: ignore
from django.core.validators import MaxValueValidator, MinValueValidator
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError


#----------------------------------- Usuário ---------------------------------------------------


class ReptilerUser(models.Model):
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

    def change_password(self, new_password: str):
        """
        Altera a senha do usuário após validar com os validadores do Django.
        Retorna uma tupla: (sucesso: bool, mensagem: str ou lista de erros)
        """
        try:
            validate_password(new_password, user=self.user)
        except ValidationError as e:
            return False, e.messages

        self.user.set_password(new_password)
        self.user.save()
        return True, "Senha alterada com sucesso!"


#----------------------------------- Fim Usuário ------------------------------------------------

#----------------------------------- Vídeo ---------------------------------------------------
#from django.dispatch import receiver



class Video(models.Model):
    """Modelo para armazenar vídeos."""
    
    reptiler_user = models.ForeignKey('ReptilerUser', on_delete=models.CASCADE, related_name='videos')
    """Relaciona o vídeo com um usuário do Reptiler."""
    
    title = CharField(max_length=200)
    description = CharField(max_length=500, blank=True, null=True)
    video_file = models.FileField(upload_to='videos/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed_video = models.FileField(upload_to='processed_videos/', blank=True, null=True)
    signal = models.FileField(upload_to='signals/', blank=True, null=True)
    plot = models.FileField(upload_to='plots/', blank=True, null=True)
    thumbnail = models.ImageField(upload_to='thumbnails/', blank=True, null=True)
    
    progresso = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Progresso do processamento em porcentagem"
    )
    
    def __str__(self):
        return self.title
#----------------------------------- Fim Vídeo ---------------------------------------------------