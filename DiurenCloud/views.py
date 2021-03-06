import hashlib

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files import File
from django.http import JsonResponse, HttpRequest
from django.shortcuts import render
from django.urls import reverse
from django.utils.decorators import method_decorator

from django.utils.translation import gettext, gettext_lazy as _
# Create your views here.
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from django.views.generic import TemplateView, DetailView

from DiurenCloud.apps import logger
from DiurenCloud.models import CloudFile
from DiurenUtility.views import LoginRequiredAPIMixin


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


# class GetObjectMixin:
#     # todo 把下边这几个视图类的共用部分抽象一波
#     def get_object(self, pk_kwarg_name: str = 'pk'):
#         pk = self.kwargs.get(pk_kwarg_name)
#         return self.model.objects.get(pk=pk)


class CloudFileDownloadRequestAPI(LoginRequiredAPIMixin, View):
    model = CloudFile

    def get_object(self):
        pk = self.kwargs.get('pk')
        return self.model.objects.get(pk=pk)

    def get(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
        except self.model.DoesNotExist:
            data = {
                'message': _('文件不存在。'),
                'code': 'file-does-not-exist',
            }
            return JsonResponse(data, status=404)
        cloud_file = self.object  # type:CloudFile
        if cloud_file.uploaded:
            data = {
                'message': _('成功生成下载url。'),
                'code': 'download-url-generated',
                'url': cloud_file.url,
            }
            return JsonResponse(data, status=200)
        else:
            data = {
                'message': _('文件尚未上传。'),
                'code': 'file-not-uploaded',
            }
            return JsonResponse(data, status=404)


class CloudFileUploadRequestAPI(LoginRequiredAPIMixin, View):
    model = CloudFile

    def get_object(self):
        pk = self.kwargs.get('pk')
        return self.model.objects.get(pk=pk)

    def get(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
        except self.model.DoesNotExist:
            data = {
                'message': _('文件不存在。'),
                'code': 'file-does-not-exist',
            }
            return JsonResponse(data, status=404)
        data = {
            'message': _('成功生成上传url。'),
            'code': 'upload-link-generated',
        }
        if settings.USE_OSS:
            pass  # todo 看看oss怎么给post链接签名
        else:
            data.update({
                'url': reverse('DiurenCloud:api-upload', kwargs={'pk': self.object.pk})
            })
        return JsonResponse(data, status=200)

'''
通过应用服务器直接上传文件
注意：需通过 Cookie 提供 sessionid
注意：需要设置 Content-type: multipart/form-data
注意：接口会对上传的文件名、文件大小和MD5进行校验

调用方法：
{"file":<文件>}
'''


@method_decorator(csrf_exempt, 'dispatch')
class CloudLocalFileUploadAPI(LoginRequiredAPIMixin, View):
    model = CloudFile

    def get_object(self):
        pk = self.kwargs.get('pk')
        return self.model.objects.get(pk=pk)

    @staticmethod
    def md5(file: File):
        logger.debug('本地上传：MD5验证计算开始')
        hasher = hashlib.md5()
        hasher.update(file.read())
        result = hasher.hexdigest()
        logger.debug('本地上传：MD5计算结果 {md5}'.format(md5=result))
        return result

    def post(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
        except self.model.DoesNotExist:
            data = {
                'message': _('文件不存在。'),
                'code': 'file-does-not-exist',
            }
            return JsonResponse(data, status=404)

        cloud_file = self.object  # type:CloudFile

        req = self.request  # type:HttpRequest
        file = req.FILES['file']

        # todo 好大一坨...想办法改改
        c_name = cloud_file.virtual_name
        logger.debug('本地上传：验证文件名 {name1} {name2}'.format(name1=file.name, name2=c_name))
        if file.name == c_name:
            c_size = cloud_file.size
            logger.debug('本地上传：验证大小 {size1} {size2}'.format(size1=file.size, size2=c_size))
            if file.size == c_size:
                file_md5 = self.md5(file)
                c_md5 = cloud_file.md5
                logger.debug('本地上传：验证MD5 {md51} {md52}'.format(md51=file_md5, md52=c_md5))
                if file_md5 == c_md5:
                    logger.debug('本地上传：验证通过√')
                    if cloud_file.uploaded:
                        msg = _('成功上传并替换当前文件。')
                        del cloud_file.file
                    else:
                        msg = _('成功上传文件。'),
                    cloud_file.file = file
                    logger.debug('本地上传：保存完成，实际保存路径 {name}'.format(name=cloud_file.path))
                else:
                    data = {
                        'message': _('文件md5校验失败。'),
                        'code': 'file-md5-validation-failed',
                    }
                    return JsonResponse(data, status=400)
            else:
                data = {
                    'message': _('文件大小校验失败。'),
                    'code': 'file-size-validation-failed',
                }
                return JsonResponse(data, status=400)
        else:
            data = {
                'message': _('文件名称校验失败。'),
                'code': 'file-name-validation-failed',
            }
            return JsonResponse(data, status=400)

        data = {
            'message': msg,
            'code': 'file-uploaded',
            'url': cloud_file.url,
        }
        try:
            cloud_file.full_clean()
        except ValidationError as e:
            data = {
                'message': _('模型验证时发生错误。'),
                'code': 'model-validation-error',
                'error': dict(e),
            }
            return JsonResponse(data, status=400)
        else:
            cloud_file.save()

            return JsonResponse(data, status=204)
