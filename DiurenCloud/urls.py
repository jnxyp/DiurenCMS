from django.urls import path, include, re_path

from DiurenCloud import views
from DiurenAccount.apps import TOKEN_LENGTH

app_name = 'DiurenCloud'

urlpatterns = [
    # 文件夹/文件显示页
    path('file/<int:pk>', views.CloudFileView.as_view(), name='file'),
    path('directory/<int:pk>', views.CloudDirectoryView.as_view(), name='directory'),
    # 上传下载授权接口
    path('api/require-upload/<int:pk>', views.CloudFileUploadRequestAPI.as_view(),
         name='api-upload-request'),
    path('api/require-download/<int:pk>', views.CloudFileDownloadRequestAPI.as_view(),
         name='api-download-request'),
    # 本地上传接口
    path('api/local-upload/<int:pk>', views.CloudLocalFileUploadAPI.as_view(), name='api-upload'),
]
