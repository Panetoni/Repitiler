from .models import ReptilerUser
from .forms import ReptilerUserForm, ReptilerUserRegisterForm, ReptilerUserLoginForm, ReptilerUserUpdateForm, VideoForm
from django.shortcuts import render, redirect # type: ignore
from django.contrib.auth import authenticate, login, logout # type: ignore
from django.contrib.auth.decorators import login_required # type: ignore





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

# Dashboard view for ReptilerUser
@login_required
def dashboard(request):
    try:
        reptiler_user = request.user.reptiler_user
    except ReptilerUser.DoesNotExist:
        return render(request, 'dashboard.html', {
            'error_message': 'Usuário sem perfil registrado. Por favor, contate o administrador.'
        })

    videos = reptiler_user.videos.all()

    # Inicializa os forms vazios
    user_form = ReptilerUserUpdateForm(request.POST or None, instance=reptiler_user)
    video_form = VideoForm(request.POST or None, request.FILES or None)

    if request.method == 'POST':
        if 'save_name_public' in request.POST and user_form.is_valid():
            user_form.save()
            return redirect('dashboard')
        elif 'upload_video' in request.POST and video_form.is_valid():
            novo_video = video_form.save(commit=False)
            novo_video.reptiler_user = reptiler_user
            novo_video.save()
            return redirect('dashboard')

    return render(request, 'dashboard.html', {
        'reptiler_user': reptiler_user,
        'videos': videos,
        'user_form': user_form,
        'video_form': video_form,
    })

# Home view 
def home(request):
    return render(request, 'home.html')

# Logout the ReptilerUser
def logoutReptilerUser(request):
    logout(request)
    return redirect('login')  # redireciona para a página de login após logout




