from django.shortcuts import render

def sign_in(request):
    return render(request, 'authentcat_app/sign_in.html')


def password_reset(request):
    return render(request, 'authentcat_app/password_reset.html')

def insert_phoneEmail(request):
    return render(request, 'authentcat_app/insert_phoneEmail.html')

def logout(request):
    return render(request, 'authentcat_app/logout.html')


def profile(request):
    return render(request, 'authentcat_app/profile.html')


def change_password(request):
    return render(request, 'authentcat_app/change_password.html')




