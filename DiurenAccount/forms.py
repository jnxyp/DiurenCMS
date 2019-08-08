import time

from django.contrib.auth.forms import UserCreationForm, UsernameField
from django.contrib.auth.models import User
from django import forms
from django.core.exceptions import ValidationError
from django.forms import ClearableFileInput
from django.utils.translation import gettext, gettext_lazy as _

from DiurenAccount.apps import EMAIL_VALIDATION_COOLDOWN
from DiurenUtility.widgets import BootstrapClearableFileInput


class UserCreationFormWithEmail(UserCreationForm):
    class Meta:
        model = User
        fields = ("username", "email")
        field_classes = {'username': UsernameField}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.error_messages['email_not_unique'] = _('邮箱已被其他用户使用。')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).count() != 0:
            raise forms.ValidationError(
                self.error_messages['email_not_unique'],
                code='email_not_unique',
            )
        return email

    def save(self, commit=True, **kwargs):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]

        if commit:
            user.save()
            # 发送邮箱验证邮件
            user.profile.send_email_validation_mail(kwargs['extra_email_context'],
                                                    kwargs['request'])
        return user


class EmailChangeForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("email",)

    resend_validation_email = forms.BooleanField(initial=False, widget=forms.HiddenInput(),
                                                 required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean(self):
        if self.data['resend_validation_email'] or 'email' in self.changed_data:
            # 检查现在是否可以发送验证邮件（验证邮件发送间隔检查）
            last_sent = self.instance.profile.last_validation_mail_sent
            if int(time.time()) - last_sent < EMAIL_VALIDATION_COOLDOWN:
                raise forms.ValidationError(
                    _('验证邮件发送过于频繁，请稍后再试。'),
                    code='validation_mail_throttling',
                )

            if self.instance.profile.email_activated:
                raise forms.ValidationError(
                    _('此邮箱已经通过验证，不需要重新发送验证邮件。')
                )
        return super().clean()

    def clean_email(self):
        # 检查邮箱地址是否重复
        email = self.cleaned_data.get('email')
        q = User.objects.filter(email=email)
        if q.count() != 0:
            if q.first() != self.instance:
                raise forms.ValidationError(
                    _('邮箱已被其他用户使用。'),
                    code='email_not_unique',
                )
        return email

    def save(self, commit=True, **kwargs):
        user = self.instance
        used_emails = user.profile.used_emails

        if self.data['resend_validation_email']:
            # 发送邮箱验证邮件
            user.profile.send_email_validation_mail(kwargs['extra_email_context'],
                                                    kwargs['request'])
        elif 'email' in self.changed_data:
            old_email = user.email
            activated = user.profile.email_activated

            # 更新邮箱账号
            user.email = self.cleaned_data["email"]
            # 记录曾用邮箱账号，虽然也不知道有什么卵用
            used_emails[old_email] = {'activated': activated}
            # 将当前邮箱激活状态设为否
            user.profile.email_activated = False
            # 发送邮箱验证邮件
            user.profile.send_email_validation_mail(kwargs['extra_email_context'],
                                                    kwargs['request'])

        if commit:
            user.profile.save()
            user.save()
        return user


class AvatarUploadForm(forms.Form):
    avatar = forms.ImageField(required=False, label=_('上传头像'),
                              widget=BootstrapClearableFileInput(ignore_initial=True))


# class AvatarCropForm(forms.Form):
#     crop_x = forms.FloatField(widget=forms.HiddenInput(), required=False)
#     crop_y = forms.FloatField(widget=forms.HiddenInput(), required=False)
#     crop_width = forms.FloatField(widget=forms.HiddenInput(), required=False)
#     crop_height = forms.FloatField(widget=forms.HiddenInput(), required=False)
#
#     class Media:
#         css = {
#             'all': ('cropper/cropper.css',)
#         }
#         js = ('cropper/cropper.js',)
