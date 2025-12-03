# serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import ReptilerUser, Video

class RegisterSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2', 'first_name']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError("As senhas não coincidem.")
        return data

    def create(self, validated_data):
        validated_data.pop('password2')

        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['first_name']
        )

        # 🔥 CRIA O ReptilerUser automaticamente
        ReptilerUser.objects.create(user=user)

        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

class VideoUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = ['video_file']

class ProgressoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = ['progresso']


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()