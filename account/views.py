from datetime import datetime
from account.models import Consumer
from django.contrib.auth import login, logout
from django.http import JsonResponse
from django.shortcuts import render, redirect
import re

def get_captcha(request):
    mobile = request.GET.get('mobile')
    user = Consumer.objects.filter(mobile=mobile).first()
    if user is None:
        user = Consumer.objects.create(mobile=mobile, username=mobile)
    user.generate_captcha()
    return JsonResponse({'msg': 'successfully'})

def login_user(request):
    if request.method == 'POST':
        mobile = request.POST.get('mobile')
        captcha = request.POST.get('captcha')
        mobile = re.sub(r'\D', '',mobile)
        user = Consumer.objects.filter(mobile=mobile).first()
        if user and user.check_captcha(captcha):
            login(request, user)
            user.login_at = datetime.now()
            user.save()
            return redirect('home')
    return render(request,'sign_in.html')

def logout_user(request):
    logout(request)
    return redirect('home')