from django.shortcuts import render, render_to_response


# Create your views here.

def index(request):
	return render_to_response("base/index.html")

def about(request):
	return render_to_response("base/about.html")

def coding(request):
	return render_to_response("base/coding.html")

def photography(request):
	return render_to_response("base/photography.html")

def contact(request):
	return render_to_response("base/contact.html")

