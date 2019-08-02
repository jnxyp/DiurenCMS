from django.urls import path, include

from DiurenUtility import views

app_name = 'DiurenUtility'
urlpatterns = [
    path('demo', views.DemoView.as_view(), name='demo')
]
