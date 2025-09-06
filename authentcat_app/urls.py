from . import views
from django.urls import path

app_name = 'authentcat_app'  # مهم لتجنب التعارض بين التطبيقات

urlpatterns = [
    path('', views.sign_in, name='sign_in'),
    path('password_reset/', views.password_reset, name='password_reset'),   
    path('insert_phoneEmail/', views.insert_phoneEmail, name='insert_phoneEmail'),      
    path('show_profile/', views.show_profile, name='show_profile'),      
    path('update_profile/', views.update_profile, name='update_profile'),      
    path('logout/', views.logout_fun, name='logout_fun'),      
    path('profile/', views.profile, name='profile'),      
    path('change_password/', views.change_password, name='change_password'),      
]