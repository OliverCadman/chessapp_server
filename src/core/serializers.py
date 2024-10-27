from rest_framework import serializers
from core.models import Room, Player, User
from django.db.models import Q


class AuthUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ["email"]


class PlayerSerializer(serializers.ModelSerializer):

    user = AuthUserSerializer(source="auth_user")
    
    class Meta:
        model = Player
        fields = ["user"]


class RoomSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        self.current_user_email = kwargs.pop("current_user_email", None)
        super(RoomSerializer, self).__init__(*args, **kwargs)

    players = serializers.SerializerMethodField()

    def get_players(self, _):
        
        qs = Player.objects.filter(~Q(auth_user__email=self.current_user_email))
        serializer = PlayerSerializer(qs, many=True)
        return serializer.data

    class Meta:
        model = Room
        fields = ["room_name", "players"]
