from django.db import models


# Create your models here.
class Game(models.Model):
    codeword = models.CharField(max_length=50)
    current_president = models.OneToOneField('Player', on_delete=models.CASCADE, related_name='role', null=True)
    current_chancellor = models.OneToOneField('Player', on_delete=models.CASCADE, related_name='+', null=True)
    turn_no = models.IntegerField(default=1)
    current_state = models.CharField(max_length=20, default='pre_game')
    elected_policies = models.CharField(max_length=200, default='[]')
    remaining_policies = models.CharField(max_length=200, default='[1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]')

    def __str__(self):
        return self.codeword


class Player(models.Model):
    name = models.CharField(max_length=50)
    game = models.ForeignKey('Game', on_delete=models.SET_NULL, null=True, related_name='players')
    voted = models.BooleanField(default=False)

    def __str__(self):
        return self.name
