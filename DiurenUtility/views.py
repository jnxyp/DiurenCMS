from django.shortcuts import render

# Create your views here.
from django.views.generic import TemplateView


class DemoView(TemplateView):
    template_name = 'utility/demo.html'
