# ================= Django =================
from django.shortcuts import render, redirect  # type: ignore
from django.contrib.auth import authenticate, login, logout, get_user_model  # type: ignore
from django.contrib.auth.decorators import login_required  # type: ignore
from django.contrib.auth.forms import SetPasswordForm
from django.contrib import messages
from django.urls import reverse
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.core.files import File
from django.conf import settings
from django.http import JsonResponse

from rest_framework.decorators import api_view
from rest_framework.response import Response





# ================= Terceiros =================
import subprocess
import cv2
import torch
import os
import math
import io
import numpy as np
import pandas as pd
import plotly.express as px
from PIL import Image
import warnings

# ================= Locais =================
from .models import ReptilerUser, Video
from .forms import (
    ReptilerUserForm,
    ReptilerUserRegisterForm,
    ReptilerUserLoginForm,
    ReptilerUserUpdateForm,
    VideoForm,
    ChangePasswordForm,
    PasswordResetRequestForm,
)

# ================= Tokens =================
from django.contrib.auth.tokens import default_token_generator

# ================= Configurações =================
# Ignora apenas FutureWarnings (como os do PyTorch)
warnings.simplefilter(action='ignore', category=FutureWarning)


# Register a new ReptilerUser
def registerReptilerUser(request):
    if request.method == 'POST':
        form = ReptilerUserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')  # redireciona após sucesso
    else:
        form = ReptilerUserRegisterForm()

    return render(request, 'signup.html', {'form': form})

# Login an existing ReptilerUser
def loginReptilerUser(request):
    if request.method == 'POST':
        form = ReptilerUserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password) 
            if user is not None:
                login(request, user)
                return redirect('dashboard')  # redireciona para o dashboard após login
            else:
                form.add_error(None, "Usuário ou senha inválidos.")
    else:
        form = ReptilerUserLoginForm()

    return render(request, 'login.html', {
        'form': form,
        'password_reset_url': reverse('password_reset_request'),  # adiciona URL para esqueci a senha
    })


@login_required
def video_progress(request, video_id):
    video = Video.objects.get(id=video_id, reptiler_user=request.user.reptiler_user)
    return JsonResponse({'progresso': video.progresso})
 
# ================= Dashboard =================
@login_required
def dashboard(request):
    try:
        reptiler_user = request.user.reptiler_user
    except ReptilerUser.DoesNotExist:
        return render(request, 'dashboard.html', {
            'error_message': 'Usuário sem perfil registrado. Por favor, contate o administrador.'
        })

    videos = reptiler_user.videos.all()
    # Lê o conteúdo do HTML do plot para cada vídeo
    for video in videos:
        if video.plot:
            with video.plot.open('r') as f:
                video.plot_html = f.read()

    return render(request, 'dashboard.html', {
        'reptiler_user': reptiler_user,
        'videos': videos,
    })


# ================= Atualizar Nome Público =================
@login_required
def update_name_public(request):
    try:
        reptiler_user = request.user.reptiler_user
    except ReptilerUser.DoesNotExist:
        messages.error(request, 'Usuário sem perfil registrado.')
        return redirect('dashboard')

    if request.method == 'POST':
        form = ReptilerUserUpdateForm(request.POST, instance=reptiler_user)
        if form.is_valid():
            form.save()
            messages.success(request, "Nome público atualizado!")
            return redirect('dashboard')
        else:
            messages.error(request, "Erro ao atualizar nome público. Confira os dados.")
    else:
        form = ReptilerUserUpdateForm(instance=reptiler_user)

    return render(request, 'update_name_public.html', {'form': form})


# ================= Alterar Senha =================
@login_required
def change_password(request):
    try:
        reptiler_user = request.user.reptiler_user
    except ReptilerUser.DoesNotExist:
        messages.error(request, 'Usuário sem perfil registrado.')
        return redirect('dashboard')

    if request.method == 'POST':
        form = ChangePasswordForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data['new_password']
            success, msg = reptiler_user.change_password(new_password)
            if success:
                messages.success(request, msg)
                return redirect('dashboard')
            else:
                for m in msg:
                    messages.error(request, m)
    else:
        form = ChangePasswordForm()

    return render(request, 'change_password.html', {'form': form})

@login_required
def upload_video(request):
    try:
        reptiler_user = request.user.reptiler_user
    except ReptilerUser.DoesNotExist:
        messages.error(request, 'Usuário sem perfil registrado.')
        return redirect('dashboard')

    if request.method == 'POST':
        form = VideoForm(request.POST, request.FILES)
        if form.is_valid():
            novo_video = form.save(commit=False)
            novo_video.reptiler_user = reptiler_user
            novo_video.progresso = 0
            novo_video.save()

            video_path = novo_video.video_file.path

            # === PROCESSAMENTO YOLO ===
            model = torch.hub.load(
                f"{settings.BASE_DIR}/yolov5",
                'custom',
                path=f"{settings.BASE_DIR}/best.pt",
                source='local',
                device='cpu'
            )
            model.conf = 0.25

            cap = cv2.VideoCapture(video_path)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            temp_out_path = os.path.join(settings.MEDIA_ROOT, "processed_videos", f"temp_proc_{novo_video.id}.mp4")
            final_out_path = os.path.join(settings.MEDIA_ROOT, "processed_videos", f"proc_{novo_video.id}.mp4")
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            writer = cv2.VideoWriter(temp_out_path, fourcc, 30.0, (width, height))

            coef_list = []
            frame_idx = 0
            success, frame = cap.read()

            while success:
                frame_idx += 1
                if frame is None:
                    success, frame = cap.read()
                    continue

                results = model(frame)
                points = dict()

                for result in results.pandas().xyxy[0].values:
                    x_min, y_min, x_max, y_max = map(round, result[:4])
                    class_id = result[6]
                    points[class_id] = (x_min, y_min, x_max, y_max)
                    if ("head" in points) and ("body" in points):
                        break

                if ("head" in points) and ("body" in points):
                    x_mean_head = int((points['head'][0] + points['head'][2]) / 2)
                    y_mean_head = int((points['head'][1] + points['head'][3]) / 2)
                    x_mean_body = int((points['body'][0] + points['body'][2]) / 2)
                    y_mean_body = int((points['body'][1] + points['body'][3]) / 2)

                    cv2.rectangle(frame, (points['head'][0], points['head'][1]),
                                  (points['head'][2], points['head'][3]), (255, 0, 0), 2)
                    cv2.rectangle(frame, (points['body'][0], points['body'][1]),
                                  (points['body'][2], points['body'][3]), (255, 0, 0), 2)
                    cv2.line(frame, (x_mean_head, y_mean_head),
                             (x_mean_body, y_mean_body), (0, 255, 0), 2)

                    dist = ((x_mean_head - x_mean_body)**2 + (y_mean_head - y_mean_body)**2)**0.5
                    coef_list.append(dist)

                # <<< ESCREVE TODOS OS FRAMES >>>
                writer.write(frame)

                novo_video.progresso = int((frame_idx / total_frames) * 100)
                novo_video.save(update_fields=['progresso'])

                success, frame = cap.read()

            cap.release()
            writer.release()

            # Converter para H.264/AAC
            subprocess.run([
                "ffmpeg", "-y", "-i", temp_out_path,
                "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-c:a", "aac", "-b:a", "128k",
                final_out_path
            ], check=True)

            # Salvar vídeo processado
            with open(final_out_path, 'rb') as f:
                novo_video.processed_video.save(f"proc_{novo_video.id}.mp4", File(f))
            os.remove(temp_out_path)

            # CSV e plot
            df = pd.Series(coef_list).fillna(0)
            csv_path = final_out_path.replace(".mp4", ".csv")
            df.to_csv(csv_path, index=False)
            with open(csv_path, 'rb') as f:
                novo_video.signal.save(f"signal_{novo_video.id}.csv", File(f))

            fig = px.line(df)
            html_path = final_out_path.replace(".mp4", ".html")
            fig.write_html(html_path)
            with open(html_path, 'rb') as f:
                novo_video.plot.save(f"plot_{novo_video.id}.html", File(f))

            # Thumbnail
            cap = cv2.VideoCapture(video_path)
            ret, frame = cap.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(frame)
                thumb_io = io.BytesIO()
                pil_img.save(thumb_io, 'JPEG')
                novo_video.thumbnail.save(f"thumb_{novo_video.id}.jpg", File(thumb_io))
            cap.release()

            novo_video.progresso = 100
            novo_video.save(update_fields=['progresso'])
            #messages.success(request, "Vídeo enviado e processado com sucesso!")
            return redirect('dashboard')

        #else:
            #messages.error(request, "Erro ao enviar vídeo.")
    else:
        form = VideoForm()

    return render(request, 'upload_video.html', {'form': form})

def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('login')

# Logout the ReptilerUser
def logoutReptilerUser(request):
    logout(request)
    return redirect('login')  # redireciona para a página de login após logout

#:@login_required
def password_reset_request(request):
    User = get_user_model() 
    if request.method == "POST":
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            associated_users = User.objects.filter(email=email)
            if associated_users.exists():
                for user in associated_users:
                    # Criar token seguro
                    token = default_token_generator.make_token(user)
                    uid = urlsafe_base64_encode(force_bytes(user.pk))
                    # URL de reset
                    reset_url = request.build_absolute_uri(
                        f"/reset/{uid}/{token}/"
                    )
                    # Render do email
                    subject = "Recuperação de senha"
                    message = render_to_string("password_reset_email.html", {
                        "user": user,
                        "reset_url": reset_url,
                    })
                    send_mail(subject, message, None, [user.email], fail_silently=False)
                messages.success(request, "Link de recuperação enviado para seu email.")
                return redirect("login")
            else:
                messages.error(request, "Nenhum usuário encontrado com esse email.")
    else:
        form = PasswordResetRequestForm()
    return render(request, "password_reset_request.html", {"form": form})


def password_reset_confirm(request, uidb64, token):
    User = get_user_model()
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == "POST":
            form = SetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Senha alterada com sucesso!")
                return redirect("http://localhost:4200/login")
        else:
            form = SetPasswordForm(user)
        return render(request, "password_reset_confirm.html", {"form": form})
    else:
        messages.error(request, "Link inválido ou expirado.")
        return redirect("password_reset_request")
    


from django.shortcuts import redirect
import jwt
from django.conf import settings

from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import redirect

def redirect_with_token(request):
    user = request.user  # já vem logado pelo allauth/google

    # Gera token JWT padrão do SimpleJWT
    refresh = RefreshToken.for_user(user)
    access = str(refresh.access_token)

    return redirect(f"http://localhost:4200/auth/callback?token={access}&refresh={refresh}")
