from django.shortcuts import render
from django.http import HttpResponse, StreamingHttpResponse
import time

from .models import Game


# Create your views here.
def index(request):
    return HttpResponse("Hello, world. You're at the SecretHitler index.")


def game(request, game_slug):
    g = Game.objects.get(slug=game_slug)
    context = {'game': g}
    return render(request, 'game/game.html', context)


def stream(request, game_slug):
    g = Game.objects.get(slug=game_slug)

    def event_stream():
        while True:
            time.sleep(3)
            yield f"data: The server time is: {g.players}\n\n"
    return StreamingHttpResponse(event_stream(), content_type='text/event-stream')
