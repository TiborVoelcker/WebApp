import json, random, os
from .models import Game

basedir = os.path.abspath(os.path.dirname(__file__))


def make_slug():
    dir = os.path.join(basedir, 'short_words.json')
    with open(dir) as f:
        words = json.load(f)
        slug = "_".join(random.choices(words, k=3))
    if Game.query.get(slug):
        slug = make_slug()

    return slug
