from django.urls import path
from .views import ask_game

app_name = 'recommendations'

urlpatterns = [
    path('ask-game/', ask_game, name='ask_game'),
]
