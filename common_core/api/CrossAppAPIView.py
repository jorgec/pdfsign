from django.db import IntegrityError
from rest_framework import permissions, status
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView


class CrossAppAPIView(APIView):
    permission_classes = [permissions.AllowAny]
    source_app_url = None
    source_app_id = None
    source_app_key = None
    model = None
    serializer = None

    def required_checks(self):
        if not self.source_app_id:
            raise AttributeError("App ID is required")

        if not self.source_app_key:
            raise AttributeError("App Key is required")

        if not self.model:
            raise AttributeError("model is required")

        if not self.serializer:
            raise AttributeError("serializer is required")

