from rest_framework import serializers
from .models import Project
from django.contrib.auth import get_user_model

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']
        ref_name = 'ProjectUserSerializer'


class ProjectSerializer(serializers.ModelSerializer):
    creator = UserSerializer(read_only=True)
    members = UserSerializer(many=True, read_only=True)

    class Meta:
        model = Project
        fields = ['id', 'name', 'description', 'creator', 'members', 'created_at', 'updated_at']
        read_only_fields = ['creator', 'created_at', 'updated_at']

    def create(self, validated_data):
        user = self.context['request'].user
        project = Project.objects.create(creator=user, **validated_data)
        project.members.add(user)
        return project


class APIResponseSerializer(serializers.Serializer):
    """API统一响应格式的序列化器"""
    status = serializers.ChoiceField(choices=['success', 'error'])
    code = serializers.IntegerField()
    message = serializers.CharField()
    data = serializers.DictField(default=dict)
    errors = serializers.DictField(default=dict) 