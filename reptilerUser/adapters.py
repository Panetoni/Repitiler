# File: Repitiler/reptilerUser/adapters.py
from allauth.account.adapter import DefaultAccountAdapter
from django.http import HttpResponseNotFound

class NoSignupLoginAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request):
        # Bloqueia o cadastro
        return False

    def login(self, request, user):
        # Bloqueia login tradicional
        raise Exception("Login desativado nesta tela. Utilize a tela padrão de login")
