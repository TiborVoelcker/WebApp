from django.shortcuts import render
from django.http import HttpResponse

from .models import Game


# Create your views here.
def index(request):
    return HttpResponse("Hello, world. You're at the SecretHitler index.")


def game(request, game_slug):
    g = Game.objects.get(slug=game_slug)
    context = {'game': g}
    return render(request, 'game/game.html', context)
