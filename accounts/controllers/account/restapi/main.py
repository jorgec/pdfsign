import json

import jwt
import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.urls import reverse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from accounts.models import ShkolaModuleMembership, ShkolaModule, ShkolaModuleRole
from accounts.models.account.serializers import AccountLoginResponseSerializer
from shkola_core.settings import config


@api_view(['GET'])
def check_email(request):
    email = request.query_params.get('email')
    try:
        check = get_user_model().objects.get(email=email)
    except get_user_model().DoesNotExist:
        check = False

    return Response(data=not check, status=status.HTTP_200_OK)


@api_view(['GET'])
def check_username(request):
    username = request.query_params.get('username')
    try:
        check = get_user_model().objects.get(username=username)
    except get_user_model().DoesNotExist:
        check = False

    return Response(data=not check, status=status.HTTP_200_OK)


@api_view(['POST'])
def relogin(request):
    refresh = request.data.get('refresh')
    decoded = jwt.decode(refresh, key=settings.SECRET_KEY, algorithms=["HS256"])

    try:
        user = get_user_model().objects.get(id=decoded.get('user_id', None))
    except KeyError:
        return Response(status=status.HTTP_404_NOT_FOUND)

    token_endpoint = config["SITEURL"] + reverse(viewname='token_refresh')
    tokens = requests.post(token_endpoint, data={
        "refresh": refresh
    }).json()

    data = {
        'data': {
            'access_token': tokens.get('access'),
            'user_data': AccountLoginResponseSerializer(user).data,
            'groups': user.get_groups(serialize=True)
        },
        'status': status.HTTP_200_OK,
        'message': 'Relogin successful'
    }
    return Response(data=data, status=status.HTTP_200_OK)


@api_view(['POST'])
def register(request):
    username = request.data.get('username')
    password = request.data.get('password')
    email = request.data.get('email')
    role = request.data.get('role')
    module = request.data.get('module')
    message = []

    try:
        module_obj = ShkolaModule.objects.get(slug__exact=module)
    except ShkolaModule.DoesNotExist:
        module_obj = None
        message.append(f"Module {module} does not exist")

    try:
        role_obj = ShkolaModuleRole.objects.get(slug__exact=role)
    except ShkolaModuleRole.DoesNotExist:
        role_obj = None
        message.append(f"Role {role} does not exist")

    try:
        username_check = get_user_model().objects.get(
            Q(username=username) | Q(email=email)
        )
        message.append(f"That username or email is already registered")
    except get_user_model().DoesNotExist:
        pass

    try:
        membership_check = ShkolaModuleMembership.objects.get(account__username__exact=username,
                                                              shkola_module__slug__exact=module)
        message.append(f"User {username} is already registered in {module}")
    except ShkolaModuleMembership.DoesNotExist:
        if module_obj and role_obj:
            user = get_user_model().objects.create_user(
                password=password,
                username=username,
                email=email,
                module=module_obj,
                role=role_obj,
                profile=request.data.get('profile', None)
            )

            token_endpoint = config["SITEURL"] + reverse(viewname='token_obtain_pair')
            tokens = requests.post(token_endpoint, data=request.data).json()

            data = {
                'data': {
                    'access_token': tokens.get('access'),
                    'refresh_token': tokens.get('refresh'),
                    'user_data': AccountLoginResponseSerializer(user).data,
                },
                'status': status.HTTP_200_OK,
                'message': 'User creation successful'
            }

            return Response(data=data, status=status.HTTP_201_CREATED)

    return Response(data={
        'data': {},
        'status': status.HTTP_400_BAD_REQUEST,
        'message': message
    })


@api_view(['POST'])
def login(request):
    username = request.data.get('username')
    password = request.data.get('password')
    module = request.data.get('module')

    try:
        user = get_user_model().objects.get(username=username)
    except get_user_model().DoesNotExist:
        return Response(data={"message": "Invalid credentials", "status": status.HTTP_401_UNAUTHORIZED},
                        status=status.HTTP_401_UNAUTHORIZED)
    if user is None:
        return Response(data={"message": "Invalid credentials", "status": status.HTTP_401_UNAUTHORIZED},
                        status=status.HTTP_401_UNAUTHORIZED)
    if not user.check_password(password):
        return Response(data={"message": "Invalid credentials", "status": status.HTTP_401_UNAUTHORIZED},
                        status=status.HTTP_401_UNAUTHORIZED)

    if not user.has_module_perms(module):
        return Response(data={"message": "Invalid credentials", "status": status.HTTP_401_UNAUTHORIZED},
                        status=status.HTTP_401_UNAUTHORIZED)

    token_endpoint = config["SITEURL"] + reverse(viewname='token_obtain_pair')
    tokens = requests.post(token_endpoint, data=request.data).json()

    data = {
        'data': {
            'access_token': tokens.get('access'),
            'refresh_token': tokens.get('refresh'),
            'user_data': AccountLoginResponseSerializer(user).data,
        },
        'status': status.HTTP_200_OK,
        'message': 'Login successful'
    }

    return Response(data=data, status=status.HTTP_200_OK)


@api_view(['GET'])
def check_email(request):
    email = request.query_params.get('email')
    try:
        check = get_user_model().objects.get(email=email)
    except get_user_model().DoesNotExist:
        check = False

    return Response(data=not check, status=status.HTTP_200_OK)


@api_view(['GET'])
def check_username(request):
    username = request.query_params.get('username')
    try:
        check = get_user_model().objects.get(username=username)
    except get_user_model().DoesNotExist:
        check = False

    return Response(data=not check, status=status.HTTP_200_OK)


class CurrentLoggedInUser(ModelViewSet):
    queryset = get_user_model().objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = AccountLoginResponseSerializer

    def retrieve(self, request, *args, **kwargs):
        user_profile = self.queryset.get(email=request.user.email)
        serializer = AccountLoginResponseSerializer(user_profile)
        return Response({'user': serializer.data})
