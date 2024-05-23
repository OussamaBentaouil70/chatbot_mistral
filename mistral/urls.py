from django.urls import path
from .views import *

urlpatterns = [
    path('login/', login_view, name='login'),
    path('server/login/', Login.as_view(), name='server_login'),
    path('chatbot/', chatbot_view, name='chatbot'),
    path('generate_text/', generate_text, name='generate_text'),
    path('logout/', logout_view, name='logout'),
]