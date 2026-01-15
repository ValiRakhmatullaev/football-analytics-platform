"""
Sandbox importer for StatsBomb Open Data
Purpose: validate analytics logic on real football data.
NOT for production use.
"""

from datetime import datetime, date
import json
from pathlib import Path
import uuid

from django.db import transaction
from django.utils import timezone

from apps.teams.models import Team
from apps.players.models import Player
from apps.competitions.models import Match, Competition, Season, MatchTeam
from apps.events.models import Event


# =========================
# CONFIG
# =========================

MATCH_ID = 7585  # ← поменяйте на нужный матч


EVENT_TYPE_MAP = {
    "Pass": "pass",
    "Shot": "shot",
    "Interception": "interception",
    "Pressure": "pressure",
    "Duel": "duel",
    "Foul Committed": "foul",
    "Ball Recovery": "recovery",
}


# =========================
# HELPERS
# =========================

def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def extract_match(match_list: list, match_id: int) -> dict:
    for m in match_list:
        if m.get("match_id") == match_id:
            return m
    raise ValueError(f"Match {match_id} not found in matches.json")


def get_or_create_sandbox_competition(match_data: dict) -> Competition:
    competition_name = match_data["competition"]["competition_name"]
    country = match_data["competition"].get("country_name", "International")

    return Competition.objects.get_or_create(
        name=competition_name,
        country=country,
        defaults={"level": 1},
    )[0]


def get_or_create_sandbox_season(match_data: dict, competition: Competition) -> Season:
    season_name = match_data["season"]["season_name"]
    match_date = date.fromisoformat(match_data["match_date"])

    return Season.objects.get_or_create(
        competition=competition,
        name=season_name,
        defaults={
            "start_date": date(match_date.year, 1, 1),
            "end_date": date(match_date.year, 12, 31),
        },
    )[0]


def get_or_create_team(sb_team: dict, competition: Competition) -> Team:
    team_name = (
        sb_team.get("team_name")
        or sb_team.get("home_team_name")
        or sb_team.get("away_team_name")
    )

    if not team_name:
        raise ValueError(f"Cannot determine team name from: {sb_team}")

    return Team.objects.get_or_create(
        name=team_name,
        competition=competition,
        defaults={"short_name": team_name[:20]},
    )[0]


def get_or_create_player(sb_player: dict) -> Player:
    # Детерминированный UUID для игроков StatsBomb
    player_uuid = uuid.uuid5(uuid.NAMESPACE_URL, f"statsbomb-player-{sb_player['id']}")

    name = sb_player.get("name", "Unknown Player").strip()
    first_name, *last_parts = name.split(" ", 1)
    last_name = last_parts[0] if last_parts else ""

    player, _ = Player.objects.get_or_create(
        id=player_uuid,
        defaults={
            "first_name": first_name,
            "last_name": last_name,
        }
    )
    return player


# =========================
# MAIN IMPORT FUNCTION
# =========================

@transaction.atomic
def import_match(matches_json_path: Path, events_json_path: Path):
    # Загрузка данных
    match_list = load_json(matches_json_path)
    match_data = extract_match(match_list, MATCH_ID)
    events_data = load_json(events_json_path)

    # Competition & Season
    competition = get_or_create_sandbox_competition(match_data)
    season = get_or_create_sandbox_season(match_data, competition)

    # Teams
    home_team = get_or_create_team(match_data["home_team"], competition)
    away_team = get_or_create_team(match_data["away_team"], competition)

    # Match kickoff time
    kickoff_time = None
    if match_data.get("match_date") and match_data.get("kick_off"):
        dt_str = f"{match_data['match_date']} {match_data['kick_off']}"
        kickoff_time = timezone.make_aware(datetime.fromisoformat(dt_str))

    # Создаём матч
    match = Match.objects.create(
        id=uuid.uuid4(),
        season=season,
        kickoff_time=kickoff_time,
        status=Match.Status.FINISHED,
    )

    # Связываем команды с матчем
    MatchTeam.objects.bulk_create([
        MatchTeam(match=match, team=home_team, side=MatchTeam.Side.HOME),
        MatchTeam(match=match, team=away_team, side=MatchTeam.Side.AWAY),
    ])

    # Кэш игроков
    player_cache = {}
    home_team_sb_id = match_data["home_team"]["home_team_id"]

    # Подготовка событий
    events_to_create = []

    for ev in events_data:
        sb_type = ev.get("type", {}).get("name")
        if sb_type not in EVENT_TYPE_MAP and sb_type != "Shot":
            continue

        sb_team = ev.get("team")
        sb_player = ev.get("player")
        if not sb_team or not sb_player:
            continue

        # Определяем команду
        team = home_team if sb_team.get("id") == home_team_sb_id else away_team

        # Игрок
        sb_player_id = sb_player["id"]
        if sb_player_id not in player_cache:
            player_cache[sb_player_id] = get_or_create_player(sb_player)
        player = player_cache[sb_player_id]

        # Тип события
        if sb_type == "Shot":
            outcome = ev.get("shot", {}).get("outcome", {}).get("name")
            event_type = "goal" if outcome == "Goal" else "shot"
        else:
            event_type = EVENT_TYPE_MAP[sb_type]

        # Координаты
        loc = ev.get("location") or [0, 0]
        x = float(loc[0])
        y = float(loc[1])

        # Период (очень важно!)
        period = ev.get("period", 1)

        # Время в миллисекундах
        minute = ev.get("minute", 0)
        second = ev.get("second", 0)
        timestamp_ms = (minute * 60 + second) * 1000

        events_to_create.append(
            Event(
                match=match,
                team=team,
                player=player,
                event_type=event_type,
                period=period,
                x=x,
                y=y,
                timestamp_ms=timestamp_ms,
            )
        )

    # Массовое создание событий
    Event.objects.bulk_create(events_to_create, batch_size=1000)

    print(f"Успешно импортирован матч {MATCH_ID}")
    return match, home_team, away_team