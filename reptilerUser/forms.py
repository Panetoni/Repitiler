from django import forms # type: ignore
from .models import ReptilerUser, Video
from django.contrib.auth.models import User # type: ignore
from django.contrib.auth.forms import UserCreationForm # type: ignore




class ReptilerUserAdminForm(forms.ModelForm):
    name_public = forms.CharField(label="Nome público", max_length=64, required=False)
    email = forms.EmailField(label="E-mail", required=False)

    class Meta:
        model = ReptilerUser
        fields = ['user']  # os campos do model real

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            user = self.instance.user
            self.fields['name_public'].initial = f"{user.first_name} {user.last_name}".strip()
            self.fields['email'].initial = user.email

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Atualiza nome público
        full_name = self.cleaned_data.get('name_public', '')
        if full_name:
            names = full_name.strip().split(" ", 1)
            instance.user.first_name = names[0]
            instance.user.last_name = names[1] if len(names) > 1 else ''

        # Atualiza e-mail
        email = self.cleaned_data.get('email', '')
        instance.user.email = email

        instance.user.save()
        if commit:
            instance.save()
        return instance

class ReptilerUserForm(forms.ModelForm):
    """Form for RepitilerUser model."""

    name_public = forms.CharField(max_length=64, required=False)

    class Meta:
        model = ReptilerUser
        fields = ['user', 'name_public']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['name_public'].initial = f"{self.instance.user.first_name} {self.instance.user.last_name}".strip()

    def save(self, commit=True):
        instance = super().save(commit=False)
        name = self.cleaned_data.get('name_public', '')
        if name:
            names = name.strip().split(" ", 1)
            instance.user.first_name = names[0]
            instance.user.last_name = names[1] if len(names) > 1 else ''
            instance.user.save()
        if commit:
            instance.save()
        return instance      
        
class ReptilerUserRegisterForm(UserCreationForm):
    """Form for registering a new RepitilerUser along with the associated User."""

    name_public = forms.CharField(
        max_length=32,
        required=False,
        label="Nome Público",
        widget=forms.TextInput(attrs={'placeholder': 'Insira seu nome público'}),
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'name_public']

    def save(self, commit=True):
        user = super().save(commit=commit)
        name_public = self.cleaned_data.get('name_public')

        # Cria o RepitilerUser associado
        ReptilerUser.objects.create(user=user, name_public=name_public)

        return user

class ReptilerUserLoginForm(forms.Form):
    """Form for logging in a RepitilerUser."""

    username = forms.CharField(label="Username", max_length=150)
    password = forms.CharField(widget=forms.PasswordInput, label="Password")

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get("username")
        password = cleaned_data.get("password")

        if not User.objects.filter(username=username).exists():
            raise forms.ValidationError("User does not exist.")
        
        return cleaned_data

class ReptilerUserUpdateForm(forms.ModelForm):
    name_public = forms.CharField(max_length=64, required=False, label='Nome público')

    class Meta:
        model = ReptilerUser
        fields = ['user']  # Remova 'name_public' daqui!

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['name_public'].initial = f"{self.instance.user.first_name} {self.instance.user.last_name}".strip()

    def save(self, commit=True):
        instance = super().save(commit=False)
        name = self.cleaned_data.get('name_public', '')
        if name:
            names = name.strip().split(" ", 1)
            instance.user.first_name = names[0]
            instance.user.last_name = names[1] if len(names) > 1 else ''
            instance.user.save()
        if commit:
            instance.save()
        return instance

class VideoForm(forms.ModelForm):
    """Form for uploading videos."""

    class Meta:
        model = Video
        fields = ['title', 'description', 'video_file']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Enter video title'}),
            'description': forms.Textarea(attrs={'placeholder': 'Enter video description'}),
            'video_file': forms.ClearableFileInput(attrs={'accept': 'video/*'}),
        }