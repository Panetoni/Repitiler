# api_views.py
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model, authenticate, login
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import ReptilerUser, Video
from .serializers import LoginSerializer, RegisterSerializer, ProgressoSerializer, PasswordResetRequestSerializer

User = get_user_model()


# -------------------------
# Dashboard - protegido via JWT
# -------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([JWTAuthentication])
def api_dashboard(request):
    user = request.user

    try:
        reptiler_user = user.reptiler_user
    except ReptilerUser.DoesNotExist:
        return Response({"detail": "Perfil não encontrado"}, status=status.HTTP_404_NOT_FOUND)

    videos = reptiler_user.videos.all()
    videos_data = []

    for video in videos:
        plot_html = None
        if video.plot:
            with video.plot.open('r') as f:
                plot_html = f.read()

        videos_data.append({
            "id": video.id,
            "title": video.title,
            "uploaded_at": video.uploaded_at,
            "progresso": video.progresso,
            "video_file_url": request.build_absolute_uri(video.video_file.url) if video.video_file else None,
            "processed_video_url": request.build_absolute_uri(video.processed_video.url) if video.processed_video else None,
            "thumbnail_url": request.build_absolute_uri(video.thumbnail.url) if video.thumbnail else None,
            "signal_url": request.build_absolute_uri(video.signal.url) if video.signal else None,
            "plot_html": plot_html
        })

    data = {
        "reptiler_user": {
            "id": user.id,
            "username": user.username,
            "full_name": user.get_full_name(),
            "email": user.email,
            "is_social": user.socialaccount_set.exists() if hasattr(user, "socialaccount_set") else False
        },
        "videos": videos_data
    }

    return Response(data)


# -------------------------
# Login - retorna token JWT
# -------------------------
from rest_framework_simplejwt.tokens import RefreshToken

@api_view(['POST'])
@permission_classes([AllowAny])
def api_login(request):
    serializer = LoginSerializer(data=request.data)

    if serializer.is_valid():
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)

            return Response({
                "message": "Login realizado com sucesso",
                "username": user.username,
                "id": user.id,
                "access": access_token,
                "refresh": str(refresh)
            })

        return Response({"error": "Usuário ou senha inválidos"},
                        status=status.HTTP_400_BAD_REQUEST)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# -------------------------
# Registro
# -------------------------
@api_view(['POST'])
@permission_classes([AllowAny])
def api_register(request):
    serializer = RegisterSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save()
        return Response(
            {"message": "Usuário registrado com sucesso"},
            status=status.HTTP_201_CREATED
        )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# -------------------------
# Usuário atual
# -------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([JWTAuthentication])
def api_current_user(request):
    user = request.user
    return Response({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name
    })


# -------------------------
# Upload de Vídeo
# -------------------------
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([JWTAuthentication])
def api_upload_video(request):
    from django.test.client import RequestFactory
    from .views import upload_video

    if "video_file" not in request.FILES:
        return Response({"error": "Envie o campo 'video_file'."},
                        status=status.HTTP_400_BAD_REQUEST)

    factory = RequestFactory()

    django_request = factory.post(
        "/fake-upload/",
        data=request.data,
        FILES=request.FILES
    )

    django_request.user = request.user
    django_request.FILES.update(request.FILES)

    resp = upload_video(django_request)

    if hasattr(resp, "status_code") and resp.status_code in (301, 302):
        return Response({"message": "Vídeo enviado e processando"}, status=201)

    return Response({"error": "Erro ao processar vídeo"}, status=400)


# -------------------------
# Deletar vídeo
# -------------------------
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([JWTAuthentication])
def api_delete_video(request, pk):
    try:
        video = Video.objects.get(id=pk, reptiler_user__user=request.user)
    except Video.DoesNotExist:
        return Response({"error": "Vídeo não encontrado"}, status=404)

    video.delete()
    return Response({"message": "Vídeo excluído com sucesso"}, status=200)


# -------------------------
# Progresso de vídeo
# -------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([JWTAuthentication])
def api_video_progresso(request, pk):
    try:
        video = Video.objects.get(id=pk, reptiler_user__user=request.user)
    except Video.DoesNotExist:
        return Response({"error": "Vídeo não encontrado"}, status=404)

    serializer = ProgressoSerializer(video)
    return Response(serializer.data, status=200)


# -------------------------
# 🔥 API RESET DE SENHA (Angular)
# -------------------------
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.template.loader import render_to_string
from django.core.mail import send_mail

@api_view(["POST"])
@permission_classes([AllowAny])
def api_password_reset_request(request):
    serializer = PasswordResetRequestSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    email = serializer.validated_data["email"]
    users = User.objects.filter(email=email)

    if not users.exists():
        return Response(
            {"error": "Nenhum usuário encontrado com esse email."},
            status=status.HTTP_404_NOT_FOUND
        )

    for user in users:
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        reset_url = request.build_absolute_uri(
            f"/reset/{uid}/{token}/"
        )

        subject = "Recuperação de senha"
        message = render_to_string("password_reset_email.html", {
            "user": user,
            "reset_url": reset_url,
        })

        send_mail(subject, message, None, [user.email], fail_silently=False)

    return Response(
        {"message": "Link de recuperação enviado para seu email."},
        status=status.HTTP_200_OK
    )
# ================= Alterar Senha (API) =================
@api_view(["POST"])
@permission_classes([IsAuthenticated])
@authentication_classes([JWTAuthentication])
def api_change_password(request):
    user = request.user

    try:
        reptiler_user = user.reptiler_user
    except ReptilerUser.DoesNotExist:
        return Response(
            {"error": "Usuário sem perfil registrado."},
            status=status.HTTP_404_NOT_FOUND
        )

    new_password = request.data.get("new_password")

    if not new_password:
        return Response({"error": "Campo 'new_password' é obrigatório."},
                        status=400)

    success, msg = reptiler_user.change_password(new_password)

    if success:
        return Response({"message": msg}, status=200)

    return Response({"errors": msg}, status=400)


# ================= Atualizar Nome Público (API) =================
@api_view(["POST"])
@permission_classes([IsAuthenticated])
@authentication_classes([JWTAuthentication])
def api_update_name_public(request):
    user = request.user

    try:
        reptiler_user = user.reptiler_user
    except ReptilerUser.DoesNotExist:
        return Response(
            {"error": "Usuário sem perfil registrado."},
            status=status.HTTP_404_NOT_FOUND
        )

    name_public = request.data.get("name_public")

    if not name_public:
        return Response(
            {"error": "Campo 'name_public' é obrigatório."},
            status=400
        )

    reptiler_user.name_public = name_public
    reptiler_user.save()

    return Response({"message": "Nome público atualizado!"}, status=200)
