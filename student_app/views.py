from django.shortcuts import render

# Create your views here.
def home(request):
    return render(request, 'student_app/home.html')

def insert_unviercityNumber(request):
    return render(request, 'student_app/insert_unviercityNumber.html')

def instructions(request):
    return render(request, 'student_app/instructions.html')