from django.urls import path
from .views import *

urlpatterns = [
    path('generate/', generate_text, name='generate_text'),
    path('chatbot/', chatbot_view, name='chatbot'),
    path('register/', Register.as_view()),
    path('login/', Login.as_view())
]