import time

from django.contrib.auth.forms import UserCreationForm, UsernameField
from django.contrib.auth.models import User
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext, gettext_lazy as _

from DiurenAccount.apps import AVATAR_MAX_ASPECT_RATIO, AVATAR_MIN_ASPECT_RATIO, \
    EMAIL_VALIDATION_COOLDOWN
from DiurenAccount.models import UserProfile


class UserAvatarChangeForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ("avatar",)

    class Media:
        css = {
            'all': ('cropper/cropper.css',)
        }
        js = ('cropper/cropper.js',)

    crop_x = forms.FloatField(widget=forms.HiddenInput(), required=False)
    crop_y = forms.FloatField(widget=forms.HiddenInput(), required=False)
    crop_width = forms.FloatField(widget=forms.HiddenInput(), required=False)
    crop_height = forms.FloatField(widget=forms.HiddenInput(), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        avatar_field = self.fields['avatar']  # type:forms.Field
        avatar_widget = avatar_field.widget  # type:forms.ClearableFileInput
        avatar_widget.template_name = 'account/avatar_input_and_edit_widget.html'

    def clean(self):
        cleaned_data = super().clean()
        avatar = self.cleaned_data.get('avatar')
        if avatar and 'avatar' not in self.changed_data:
            x = self.data.get('crop_x')
            y = self.data.get('crop_y')
            w = self.data.get('crop_width')
            h = self.data.get('crop_height')
            if None not in (x, y, w, h):
                try:
                    x, y, w, h = [float(i) for i in [x, y, w, h]]
                except ValueError:
                    raise ValidationError(message=_('头像裁剪参数无效。'), code='crop_params')
                else:
                    if w < 10 or h < 10:  # 小于10*10的选区判定为无效
                        raise ValidationError(message=_('头像剪裁区域过小。'), code='crop_params')
                    ratio = w / h
                    if ratio > AVATAR_MAX_ASPECT_RATIO or ratio < AVATAR_MIN_ASPECT_RATIO:
                        raise ValidationError(message=_('头像比例超过限制。'), code='crop_params')
                    else:
                        cleaned_data.update({'x': x, 'y': y, 'w': w, 'h': h})
            else:
                raise ValidationError(message=_('未提供头像剪裁参数。'), code='crop_params')
        return cleaned_data

    def save(self, commit=True):
        avatar = self.cleaned_data.get('avatar')
        instance = super().save(commit)
        # 如果没有上传新的头像，根据表单数据裁剪现有头像
        if avatar and 'avatar' not in self.changed_data:
            x = self.cleaned_data.get('crop_x')
            y = self.cleaned_data.get('crop_y')
            w = self.cleaned_data.get('crop_width')
            h = self.cleaned_data.get('crop_height')

            instance.crop_avatar(x, y, w, h, True)

        return instance


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
