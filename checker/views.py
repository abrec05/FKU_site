from django.shortcuts import render

def index(request):
    return render(request, "checker/main.html")