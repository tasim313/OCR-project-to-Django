from django.contrib import admin
from django.urls import path
from ocre_app import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('upload/', views.upload_file, name='upload_file'),
    path('download/<str:format>/', views.download_file, name='download_file'),
]

