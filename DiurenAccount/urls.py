from django.urls import path, include, re_path

from DiurenAccount import views
from DiurenAccount.apps import TOKEN_LENGTH

app_name = 'DiurenAccount'

urlpatterns = [
    # 登入与登出
    path('login/', views.DiurenLoginView.as_view(), name='login'),
    path('logout/', views.DiurenLogoutView.as_view(), name='logout'),

    # 资料页
    path('user/<int:pk>', views.DiurenUserDetailView.as_view(), name='info'),
    re_path(r'^$', views.DiurenUserSelfView.as_view(), name='self'),

    # 注册
    path('register/', views.DiurenUserRegisterView.as_view(), name='register'),

    # 用户资料修改
    path('change-profile/', views.DiurenUserProfileChangeView.as_view(), name='change-profile'),
    path('change-email/', views.DiurenEmailChangeView.as_view(), name='change-email'),
    path('modify-avatar/', views.DiurenAvatarModifyView.as_view(), name='modify-avatar'),

    # 头像修改API
    # path('modify-avatar/upload', views.DiurenAvatarUploadAPI.as_view(), name='api-upload-avatar'),
    # path('modify-avatar/crop', views.DiurenAvatarCropAPI.as_view(), name='api-crop-avatar'),

    # 邮箱修改
    path('change-email/', views.DiurenEmailChangeView.as_view(), name='change-email'),
    path('change-email/done/', views.DiurenEmailChangeDoneView.as_view(), name='change-email-done'),
    re_path(r'^change-email/validate/(?P<token>[0-9A-Za-z]{%d})/$' % TOKEN_LENGTH,
            views.DiurenEmailValidateView.as_view(), name='change-email-validate'),

    # 密码修改
    path('change-password/', views.DiurenPasswordChangeView.as_view(), name='change-password'),
    path('reset-password/complete/', views.DiurenPasswordModifyCompleteView.as_view(),
         name='change-password-complete'),

    # 密码重置
    path('reset-password/', views.DiurenPasswordResetView.as_view(), name='reset-password'),
    path('reset-password/done/', views.DiurenPasswordResetDoneView.as_view(),
         name='reset-password-done'),
    re_path(
        r'^reset-password/validate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        views.DiurenPasswordResetValidateView.as_view(), name='reset-password-validate'),
    path('reset-password/complete/', views.DiurenPasswordModifyCompleteView.as_view(),
         name='reset-password-complete'),
]
