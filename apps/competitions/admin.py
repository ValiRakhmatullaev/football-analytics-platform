from django.contrib import admin
from .models import Competition, Season, Match, MatchTeam

admin.site.register(Competition)
admin.site.register(Season)
admin.site.register(Match)
admin.site.register(MatchTeam)
