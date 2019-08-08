from django.http import JsonResponse, HttpResponse
from django.shortcuts import render

# Create your views here.
from django.views.generic import TemplateView


class DemoView(TemplateView):
    template_name = 'utility/demo.html'


class LoginRequiredAPIMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            response = {
                'message': '需要登陆。',
                'code': 'login-required'
            }
            return JsonResponse(response, status=403)
        return super().dispatch(request, *args, **kwargs)
