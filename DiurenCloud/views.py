from django.shortcuts import render

# Create your views here.
from django.views import View

from django.views.generic import TemplateView, DetailView


class CloudUserSelfView(TemplateView):
    pass


class CloudUserProfileView(DetailView):
    pass


class CloudDirectoryView(TemplateView):
    pass


class CloudFileView(DetailView):
    pass


class CloudPathView(TemplateView):
    pass


class CloudFileDownloadRequestAPI(View):
    pass


class CloudFileUploadRequestAPI(View):
    pass


class CloudLocalFileUploadAPI(View):
    pass
