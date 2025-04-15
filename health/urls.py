from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path('', views.home, name='home'),
    path('register/', views.register_user, name='register'),
    path('register/admin/', views.register_admin, name='register_admin'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('schedule/', views.user_schedule, name='user_schedule'),
    path('consultation/create/', views.create_consultation, name='create_consultation'),
    path('manager/schedule/', views.admin_schedule, name='admin_schedule'),
    path('manager/consultation/create/', views.admin_create_consultation, name='admin_create_consultation'),
    path('manager/consultation/<int:pk>/assign/', views.assign_consultation, name='assign_consultation'),
    path('manager/consultation/<int:pk>/status/<str:status>/', views.update_consultation_status, name='update_consultation_status'),
]
