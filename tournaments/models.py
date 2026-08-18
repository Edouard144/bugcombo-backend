from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class Tournament(models.Model):
    STATUS_CHOICES = [
        ('upcoming', 'Upcoming'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    FORMAT_CHOICES = [
        ('single_elimination', 'Single Elimination'),
        ('double_elimination', 'Double Elimination'),
        ('round_robin', 'Round Robin'),
        ('swiss', 'Swiss'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='upcoming')
    format = models.CharField(max_length=30, choices=FORMAT_CHOICES, default='single_elimination')
    max_participants = models.IntegerField(default=16)
    min_participants = models.IntegerField(default=2)
    prize_pool = models.IntegerField(default=0)
    registration_start = models.DateTimeField()
    registration_end = models.DateTimeField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tournaments')
    participants = models.ManyToManyField(User, through='TournamentParticipant', related_name='tournaments')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

class TournamentParticipant(models.Model):
    STATUS_CHOICES = [
        ('registered', 'Registered'),
        ('checked_in', 'Checked In'),
        ('disqualified', 'Disqualified'),
        ('withdrawn', 'Withdrawn'),
    ]

    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='registered')
    seed = models.IntegerField(null=True, blank=True)
    wins = models.IntegerField(default=0)
    losses = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['tournament', 'user']
        ordering = ['seed', 'created_at']

    def __str__(self):
        return f"{self.user.username} in {self.tournament.name}"

class TournamentMatch(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='matches')
    round = models.IntegerField()
    match_number = models.IntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    participant1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tournament_matches_as_p1', null=True, blank=True)
    participant2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tournament_matches_as_p2', null=True, blank=True)
    winner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tournament_wins', null=True, blank=True)
    loser = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tournament_losses', null=True, blank=True)
    score_p1 = models.IntegerField(null=True, blank=True)
    score_p2 = models.IntegerField(null=True, blank=True)
    next_match = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='previous_matches')
    next_match_slot = models.CharField(max_length=10, choices=[('p1', 'Player 1'), ('p2', 'Player 2')], null=True, blank=True)
    duel_room = models.ForeignKey('duels.DuelRoom', on_delete=models.SET_NULL, null=True, blank=True, related_name='tournament_matches')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['round', 'match_number']
        unique_together = ['tournament', 'round', 'match_number']

    def __str__(self):
        return f"Round {self.round} Match {self.match_number} - {self.tournament.name}"
