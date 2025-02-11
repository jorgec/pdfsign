from django.db import IntegrityError
from rest_framework import permissions, status
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView


class DefaultAPIView(APIView):
    permission_classes = [permissions.AllowAny]
    permission_module = None
    model = None
    serializer = None

    def required_checks(self):
        if not self.permission_module:
            raise AttributeError("permission_module is required")

        if not self.model:
            raise AttributeError("model is required")

        if not self.serializer:
            raise AttributeError("serializer is required")

    def get(self, request, *args, **kwargs):
        self.required_checks()

        permissions_required = "view_" + self.permission_module

        try:
            if not request.user.is_admin:
                if not request.user.has_perms(permissions_required):
                    return Response(status=status.HTTP_401_UNAUTHORIZED)
        except AttributeError:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        s = request.GET.get('s', None)
        v = request.GET.get('v', None)
        like_query = request.GET.get('l', False)
        sort_order = request.GET.get('sort_order', '-')
        order_by = request.GET.get('order_by', 'created')

        if s and v:
            if like_query:
                filter_params = {f"{s}__icontains": v}
            else:
                filter_params = {s: v}
            obj_list = self.model.objects.filter(**filter_params)
        else:
            obj_list = self.model.objects.all()

        serializer = self.serializer(obj_list.order_by(f"{sort_order}{order_by}"), many=True)

        return Response(data=serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        self.required_checks()

        permissions_required = "add_" + self.permission_module

        if not request.user.is_admin:
            if not request.user.has_perms(permissions_required):
                return Response(status=status.HTTP_401_UNAUTHORIZED)

        data = request.data

        serializer = self.serializer(data=data)

        if serializer.is_valid():
            try:
                obj = self.model.objects.create(**serializer.data)
            except IntegrityError as e:
                return Response(e, status=status.HTTP_400_BAD_REQUEST)

            return_data = {
                "data": self.serializer(obj).data,
                "message": f"{obj} saved",
                "status": True
            }

            return Response(return_data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
