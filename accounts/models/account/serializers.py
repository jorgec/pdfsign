from rest_framework import serializers

from .models import Account


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Account


class AccountLoginSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ['username', 'password']
        model = Account

