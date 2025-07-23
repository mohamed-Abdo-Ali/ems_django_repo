from django.shortcuts import render

# Create your views here.
def home(request):
    return render(request, 'conttroll_app/home.html')