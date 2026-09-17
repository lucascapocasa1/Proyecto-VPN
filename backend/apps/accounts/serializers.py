from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import LeagueAdmin, ClubAdmin

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "role", "is_active", "created_at"]
        read_only_fields = ["id", "created_at"]


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["id", "username", "email", "password", "role"]
        read_only_fields = ["id"]

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()


class LeagueAdminSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    league_name = serializers.CharField(source="league.name", read_only=True)

    class Meta:
        model = LeagueAdmin
        fields = ["id", "user", "league", "username", "league_name", "created_at"]
        read_only_fields = ["id", "created_at"]


class ClubAdminSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    club_name = serializers.CharField(source="club.name", read_only=True)

    class Meta:
        model = ClubAdmin
        fields = ["id", "user", "club", "username", "club_name", "created_at"]
        read_only_fields = ["id", "created_at"]
