from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView, PasswordResetView, \
    PasswordResetConfirmView, PasswordResetDoneView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import UpdateView, DetailView, TemplateView, FormView
from DiurenAccount.forms import UserCreationFormWithEmail, EmailChangeForm, AvatarUploadForm
from DiurenAccount.models import UserProfile


class DiurenLoginView(LoginView):
    template_name = 'account/user_login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        url = self.get_redirect_url()
        if not url:
            url = reverse('DiurenAccount:self')
        return url


class DiurenLogoutView(LogoutView):
    template_name = 'account/user_logged_out.html'


class DiurenUserSelfView(TemplateView):
    template_name = 'account/user_own_detail.html'


class DiurenUserDetailView(DetailView):
    model = User
    template_name = 'account/user_detail.html'


class DiurenUserRegisterView(FormView):
    form_class = UserCreationFormWithEmail
    template_name = 'account/user_register.html'
    extra_email_context = {'SETTINGS': settings}

    def form_valid(self, form):
        opts = {
            'extra_email_context': self.extra_email_context,
            'request': self.request
        }
        user = form.save(**opts)
        login(self.request, user)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('DiurenAccount:self')


class DiurenEmailChangeView(LoginRequiredMixin, UpdateView):
    template_name = 'account/user_email_change.html'
    form_class = EmailChangeForm
    extra_email_context = {'SETTINGS': settings}

    def form_valid(self, form: EmailChangeForm):
        opts = {
            'extra_email_context': self.extra_email_context,
            'request': self.request
        }
        form.save(**opts)
        # 如果修改了邮箱/重发了邮件，重定向到验证邮件已发送页面；如果没有修改，重定向到个人资料页面。
        if 'email' in form.changed_data or form.data['resend_validation_email']:
            self.success_url = reverse('DiurenAccount:change-email-done')
        else:
            self.success_url = reverse('DiurenAccount:self')

        return HttpResponseRedirect(self.get_success_url())

    def get_object(self, queryset=None):
        return self.request.user


class DiurenEmailChangeDoneView(LoginRequiredMixin, TemplateView):
    template_name = 'account/user_email_change_done.html'


class DiurenEmailValidateView(LoginRequiredMixin, TemplateView):
    template_name = 'account/user_email_validate.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        u = self.request.user  # type:User
        profile = u.profile
        token = self.kwargs['token']

        validlink = u.profile.email_token_valid(u.email, token)
        # 如果token有效，激活用户邮箱
        if validlink:
            profile.email_activated = True
            profile.destroy_email_validation_token(token_to_destroy=token, commit=False)
            profile.save()

        context['validlink'] = validlink

        return context


class DiurenUserProfileChangeView(LoginRequiredMixin, UpdateView):
    template_name = 'account/user_profile_change.html'
    fields = ('nick', 'language')

    def get_object(self, queryset=None):
        profile = UserProfile.objects.get(user=self.request.user)
        return profile

    def get_success_url(self):
        return reverse('DiurenAccount:self')


class DiurenAvatarModifyView(LoginRequiredMixin, FormView):
    template_name = 'account/user_avatar_modify.html'
    form_class = AvatarUploadForm

    def get_success_url(self):
        return reverse('DiurenAccount:self')

    def form_valid(self, form):
        profile = self.request.user.profile  # type:UserProfile
        if not form.cleaned_data['avatar']:
            del profile.avatar
            profile.save()
        else:
            profile.avatar = form.cleaned_data['avatar']
            profile.save()
        return super().form_valid(form)


# class DiurenAvatarUploadAPI(LoginRequiredAPIMixin, View):
#
#     def post(self, request: HttpRequest, *args, **kwargs):
#         form = AvatarUploadForm(request.POST, request.FILES)
#         if form.is_valid():
#             profile = self.request.user.profile  # type:UserProfile
#             if not form.cleaned_data['avatar']:
#                 del profile.avatar
#                 profile.save()
#                 response = {
#                     'message': '头像删除成功。',
#                     'code': 'delete-avatar-success',
#                 }
#                 return JsonResponse(response, status=204)
#             else:
#                 profile.avatar = form.cleaned_data['avatar']
#                 profile.save()
#                 response = {
#                     'message': '头像设置成功。',
#                     'code': 'set-avatar-success',
#                 }
#                 return JsonResponse(response, status=201)
#         else:
#             response = {
#                 'message': '头像数据无效。',
#                 'code': 'invalid-avatar-data',
#                 'errors': form.errors
#             }
#             return JsonResponse(response, status=400)
#
#
# class DiurenAvatarCropAPI(LoginRequiredAPIMixin, View):
#     def post(self, request: HttpRequest, *args, **kwargs):
#         form = AvatarCropForm(request.POST)
#         pass


class DiurenPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    template_name = 'account/user_password_change.html'

    def get_success_url(self):
        return reverse('DiurenAccount:change-password-complete')


class DiurenPasswordResetView(PasswordResetView):
    template_name = 'account/user_password_reset.html'
    email_template_name = 'email/mail_password_reset.xhtml'
    subject_template_name = 'email/mail_password_reset_subject.txt'
    extra_email_context = {'SETTINGS': settings}

    def get_success_url(self):
        return reverse('DiurenAccount:reset-password-done')


class DiurenPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'account/user_password_reset_done.html'

    def get_success_url(self):
        return reverse('DiurenAccount:reset-password-validate')


class DiurenPasswordResetValidateView(PasswordResetConfirmView):
    template_name = 'account/user_password_reset_validate.html'

    def get_success_url(self):
        return reverse('DiurenAccount:reset-password-complete')


class DiurenPasswordModifyCompleteView(TemplateView):
    template_name = 'account/user_password_modify_done.html'
