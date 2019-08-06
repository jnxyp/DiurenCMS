from django.urls import path, include, re_path

from DiurenCloud import views
from DiurenAccount.apps import TOKEN_LENGTH

app_name = 'DiurenCloud'

urlpatterns = [
    # 资料页
    path('user/<int:pk>', views.CloudUserProfileView.as_view(), name='info'),
    re_path(r'^$', views.CloudUserSelfView.as_view(), name='self'),
    # 文件夹/文件显示页
    path('file/<int:pk>', views.CloudFileView.as_view(), name='file'),
    path('directory/<int:pk>', views.CloudDirectoryView.as_view(), name='directory'),
    path('path/<str:path>', views.CloudPathView.as_view(), name='path'),
    # 上传下载授权接口
    path('api/require-upload', views.CloudFileUploadRequestAPI, name='api-upload-request'),
    path('api/require-download', views.CloudFileDownloadRequestAPI, name='api-download-request'),
    # 本地上传接口
    path('api/local-upload', views.CloudLocalFileUploadAPI, name='api-upload'),
]
