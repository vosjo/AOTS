# Create your views here.
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.crypto import get_random_string
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .forms import ChangeProPicForm
from .models import User


class APIKeysView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = User.objects.get(id=request.user.id)
        if user:
            return Response(data={"api_key": user.api_key}, status=status.HTTP_200_OK)

    def post(self, request):
        user = User.objects.get(id=request.user.id)
        if user:
            api_key = get_random_string(
                32, allowed_chars="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
            api_secret = get_random_string(
                64, allowed_chars="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
            user.api_key = api_key
            user.api_secret = make_password(api_secret)
            user.save()
            return Response(data={"api_key": api_key, "api_secret": api_secret}, status=status.HTTP_200_OK)


class ValidateAPIKeysView(APIView):
    def post(self, request):
        api_key = request.headers.get("api-key")
        api_secret = request.headers.get("api-secret")

        try:
            user = User.objects.get(api_key=api_key)
        except:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if user:
            if user.api_key == api_key and user.has_valid_api_secret(api_secret):
                return Response(data={"valid": True}, status=status.HTTP_200_OK)
            return Response(data={"valid": False}, status=status.HTTP_200_OK)


@login_required
def thisUsersPage(request, **kwargs):
    if request.method == 'POST':
        form = ChangeProPicForm(request.POST, request.FILES)
        if form.is_valid():
            newpic = request.FILES.getlist('newpic')
            request.user.profile_picture = newpic[0]
            request.user.save()
            return HttpResponseRedirect(reverse(
                'users:personal_page',
                kwargs={},
            ))
    form = ChangeProPicForm()
    return render(request, 'users/personal_page.html', {'this_user': request.user, "form": form})


@login_required
def foreignUsersPage(request, user_id, **kwargs):
    if request.user.pk == user_id:
        return thisUsersPage(request, **kwargs)
    else:
        viewed_user = User.objects.get(pk=user_id)
        return render(request, 'users/foreigners_page.html', {'viewed_user': viewed_user})