from .models import ReptilerUser
from .forms import ReptilerUserForm, ReptilerUserRegisterForm, ReptilerUserLoginForm, ReptilerUserUpdateForm, VideoForm
from django.shortcuts import render, redirect # type: ignore
from django.contrib.auth import authenticate, login, logout # type: ignore
from django.contrib.auth.decorators import login_required # type: ignore

import subprocess
import cv2, torch, os, math, io
import numpy as np
import pandas as pd
import plotly.express as px
from PIL import Image
from django.core.files import File
from django.conf import settings
from django.http import JsonResponse
from .models import Video

import warnings

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

    return render(request, 'registerReptilerUser.html', {'form': form})

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

    return render(request, 'loginReptilerUser.html', {'form': form})


@login_required
def video_progress(request, video_id):
    video = Video.objects.get(id=video_id, reptiler_user=request.user.reptiler_user)
    return JsonResponse({'progresso': video.progresso})

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

    user_form = ReptilerUserUpdateForm(request.POST or None, instance=reptiler_user)
    video_form = VideoForm(request.POST or None, request.FILES or None)

    if request.method == 'POST':
        # Deletar vídeo
        if 'delete_video' in request.POST:
            video_id = request.POST.get('video_id')
            try:
                video_to_delete = reptiler_user.videos.get(id=video_id)
                video_to_delete.delete()
            except Video.DoesNotExist:
                pass
            return redirect('dashboard')

        # Atualizar nome público
        if 'save_name_public' in request.POST and user_form.is_valid():
            user_form.save()
            return redirect('dashboard')

        # Upload e processamento de vídeo
        elif 'upload_video' in request.POST and video_form.is_valid():
            novo_video = video_form.save(commit=False)
            novo_video.reptiler_user = reptiler_user
            novo_video.progresso = 0  # inicializa com 0%
            novo_video.save()

            video_path = novo_video.video_file.path

            # === PROCESSAMENTO YOLO ===
            model = torch.hub.load(
                f"{settings.BASE_DIR}/yolov5",
                'custom',
                path=f"{settings.BASE_DIR}/best.pt",
                source='local',
                device='gpu'
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
            x = 0.0
            y = 0.0
            frame_idx = 0
            success, frame = cap.read()
            while success:
                frame_idx += 1
                results = model(frame)
                points = dict()
                for result in results.pandas().xyxy[0].values:
                    x_min, y_min, x_max, y_max = map(round, result[:4])
                    class_id = result[6]
                    points[class_id] = (x_min, y_min, x_max, y_max)
                    if ("head" in points) and ("body" in points):
                        break

                if ("head" in points) and ("body" in points):
                    image = frame
                    x_mean_head = int((points['head'][0] + points['head'][2]) / 2)
                    y_mean_head = int((points['head'][1] + points['head'][3]) / 2)
                    x_mean_body = int((points['body'][0] + points['body'][2]) / 2)
                    y_mean_body = int((points['body'][1] + points['body'][3]) / 2)

                    # Desenho
                    cv2.rectangle(image, (points['head'][0], points['head'][1]),
                                  (points['head'][2], points['head'][3]), (255, 0, 0), 2)
                    cv2.rectangle(image, (points['body'][0], points['body'][1]),
                                  (points['body'][2], points['body'][3]), (255, 0, 0), 2)
                    cv2.line(image, (x_mean_head, y_mean_head),
                             (x_mean_body, y_mean_body), (0, 255, 0), 2)
                    writer.write(image)

                    # === cálculo do coeficiente (distância cabeça-corpo) ===
                    dist = ((x_mean_head - x_mean_body) ** 2 + (y_mean_head - y_mean_body) ** 2) ** 0.5
                    coef_list.append(dist)
                else:
                    writer.write(frame)

                # Atualiza progresso
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

            # Salvar no modelo
            novo_video.processed_video.save(f"proc_{novo_video.id}.mp4", File(open(final_out_path, 'rb')))
            os.remove(temp_out_path)

            # CSV e plot
            df = pd.Series(coef_list).fillna(0)
            csv_path = final_out_path.replace(".mp4", ".csv")
            df.to_csv(csv_path, index=False)
            novo_video.signal.save(f"signal_{novo_video.id}.csv", File(open(csv_path, 'rb')))

            fig = px.line(df)
            html_path = final_out_path.replace(".mp4", ".html")
            fig.write_html(html_path)
            novo_video.plot.save(f"plot_{novo_video.id}.html", File(open(html_path, 'rb')))

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
            return redirect('dashboard')

    return render(request, 'dashboard.html', {
        'reptiler_user': reptiler_user,
        'videos': videos,
        'user_form': user_form,
        'video_form': video_form,
    })

# Home view 

def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('login')

# Logout the ReptilerUser
def logoutReptilerUser(request):
    logout(request)
    return redirect('login')  # redireciona para a página de login após logout




