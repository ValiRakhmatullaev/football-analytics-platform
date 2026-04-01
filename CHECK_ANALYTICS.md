# Как проверить аналитику после загрузки видео

## 🎯 Быстрый способ получить ID

### Шаг 1: Получить список всех загруженных видео

```bash
GET http://127.0.0.1:8000/api/analytics/videos/
```

**Ответ:**
```json
{
  "videos": [
    {
      "id": "8999ae63-f460-45e8-b537-12e2be4fe275",
      "file_name": "second_half_60-70.mp4",
      "status": "completed",
      "events_count": 15,
      "uploaded_at": "2026-01-26T10:45:07",
      "match_id": "abc123-def456-..."
    }
  ]
}
```

### Шаг 2: Получить детальную информацию о видео

```bash
GET http://127.0.0.1:8000/api/analytics/videos/<video_id>/info/
```

**Ответ содержит:**
- ✅ **Match ID** - для аналитики матча
- ✅ **Team IDs** - для аналитики команд
- ✅ **Player IDs** - для аналитики игроков (если созданы)
- ✅ **Event statistics** - статистика событий
- ✅ **Analytics URLs** - готовые ссылки на аналитику

**Пример ответа:**
```json
{
  "video": {
    "id": "8999ae63-f460-45e8-b537-12e2be4fe275",
    "file_name": "second_half_60-70.mp4",
    "status": "completed",
    "events_count": 15
  },
  "match": {
    "id": "abc123-def456-ghi789",
    "kickoff_time": "2026-01-26T10:00:00",
    "status": "finished"
  },
  "teams": [
    {
      "team_id": "team-1-uuid",
      "team_name": "Real Madrid",
      "side": "home"
    },
    {
      "team_id": "team-2-uuid",
      "team_name": "Barcelona",
      "side": "away"
    }
  ],
  "players": [
    {
      "player_id": "player-1-uuid",
      "player_name": "John Doe",
      "position": "MF",
      "team_id": "team-1-uuid",
      "team_name": "Real Madrid",
      "minutes_played": 90
    }
  ],
  "events": {
    "total": 15,
    "by_type": {
      "pass": 10,
      "shot": 3,
      "turnover": 2
    },
    "by_team": {
      "team-1-uuid": 8,
      "team-2-uuid": 7
    }
  },
  "analytics_urls": {
    "match_overview": "/api/analytics/matches/abc123-def456-ghi789/overview/",
    "coach_summary": "/api/analytics/coach-summary/?team_id=team-1-uuid&match_ids[]=abc123-def456-ghi789",
    "player_profile": "/api/analytics/matches/abc123-def456-ghi789/players/player-1-uuid/profile/"
  }
}
```

## 📋 Пошаговая инструкция

### Вариант 1: Через браузер (самый простой)

1. **Откройте в браузере:**
   ```
   http://127.0.0.1:8000/api/analytics/videos/
   ```
   Вы увидите список всех видео с их ID и match_id

2. **Скопируйте `match_id`** из ответа

3. **Откройте аналитику матча:**
   ```
   http://127.0.0.1:8000/api/analytics/matches/<match_id>/overview/
   ```

### Вариант 2: Через curl (терминал)

```bash
# 1. Получить список видео
curl http://127.0.0.1:8000/api/analytics/videos/

# 2. Получить детальную информацию (замените VIDEO_ID)
curl http://127.0.0.1:8000/api/analytics/videos/VIDEO_ID/info/

# 3. Проверить аналитику матча (замените MATCH_ID)
curl http://127.0.0.1:8000/api/analytics/matches/MATCH_ID/overview/
```

### Вариант 3: Через Python скрипт

Создайте файл `check_analytics.py`:

```python
import requests

BASE_URL = "http://127.0.0.1:8000"

# 1. Получить список видео
response = requests.get(f"{BASE_URL}/api/analytics/videos/")
videos = response.json()["videos"]

if videos:
    video = videos[0]  # Последнее загруженное видео
    video_id = video["id"]
    match_id = video.get("match_id")
    
    print(f"Video ID: {video_id}")
    print(f"Match ID: {match_id}")
    print(f"Events: {video['events_count']}")
    
    # 2. Получить детальную информацию
    info_response = requests.get(f"{BASE_URL}/api/analytics/videos/{video_id}/info/")
    info = info_response.json()
    
    print("\n=== Детальная информация ===")
    print(f"Teams: {len(info.get('teams', []))}")
    print(f"Players: {len(info.get('players', []))}")
    print(f"Events: {info.get('events', {}).get('total', 0)}")
    
    # 3. Проверить аналитику
    if match_id:
        analytics_response = requests.get(
            f"{BASE_URL}/api/analytics/matches/{match_id}/overview/"
        )
        analytics = analytics_response.json()
        
        print("\n=== Аналитика матча ===")
        print(f"Tempo: {analytics.get('teams', {}).get('home', {}).get('metrics', {}).get('tempo', 'N/A')}")
        print(f"Home possession: {analytics.get('teams', {}).get('home', {}).get('metrics', {}).get('possession_pct', 'N/A')}%")
else:
    print("Нет загруженных видео")
```

Запустите:
```bash
python check_analytics.py
```

## 🔍 Как получить ID игрока

### Способ 1: Через API видео

```bash
GET http://127.0.0.1:8000/api/analytics/videos/<video_id>/info/
```

В ответе будет массив `players` с `player_id` для каждого игрока.

### Способ 2: Через Django shell

```bash
cd backend
python manage.py shell
```

```python
from apps.players.models import Player
from apps.competitions.models import Match

# Получить всех игроков
players = Player.objects.all()
for p in players:
    print(f"{p.id} - {p.first_name} {p.last_name}")

# Получить игроков конкретного матча
match = Match.objects.get(id="<match_id>")
from apps.players.models import Appearance
appearances = Appearance.objects.filter(match=match)
for app in appearances:
    print(f"{app.player.id} - {app.player.first_name} {app.player.last_name} - Team: {app.team.name}")
```

### Способ 3: Через админку Django

1. Откройте `http://127.0.0.1:8000/admin/`
2. Перейдите в "Players"
3. Скопируйте ID из списка

## ✅ Проверка аналитики

### 1. Обзор матча
```bash
GET http://127.0.0.1:8000/api/analytics/matches/<MATCH_ID>/overview/
```

**Что проверить:**
- ✅ `teams.home.metrics.possession_pct` - владение мячом
- ✅ `teams.home.metrics.turnovers` - потери
- ✅ `teams.home.metrics.tempo` - темп матча

### 2. Профиль игрока
```bash
GET http://127.0.0.1:8000/api/analytics/matches/<MATCH_ID>/players/<PLAYER_ID>/profile/
```

**Что проверить:**
- ✅ `event_summary` - сводка событий
- ✅ `position_metrics` - метрики по позиции
- ✅ `timeline` - временная линия событий

### 3. Тренерская аналитика
```bash
GET http://127.0.0.1:8000/api/analytics/coach-summary/?team_id=<TEAM_ID>&match_ids[]=<MATCH_ID>
```

**Что проверить:**
- ✅ `strengths` - сильные стороны
- ✅ `weaknesses` - слабые стороны
- ✅ `tactics` - тактические инсайты

## 🚀 Быстрый тест

После загрузки видео выполните:

```bash
# 1. Получить список видео
curl http://127.0.0.1:8000/api/analytics/videos/ | python -m json.tool

# 2. Скопировать match_id из ответа

# 3. Проверить аналитику
curl http://127.0.0.1:8000/api/analytics/matches/<MATCH_ID>/overview/ | python -m json.tool
```

## 💡 Полезные команды

### Получить все ID одной командой:

```bash
# Получить все ID из последнего видео
VIDEO_ID=$(curl -s http://127.0.0.1:8000/api/analytics/videos/ | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['videos'][0]['id'] if data['videos'] else '')")

# Получить match_id
MATCH_ID=$(curl -s http://127.0.0.1:8000/api/analytics/videos/$VIDEO_ID/info/ | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['match']['id'] if data.get('match') else '')")

echo "Video ID: $VIDEO_ID"
echo "Match ID: $MATCH_ID"

# Проверить аналитику
curl http://127.0.0.1:8000/api/analytics/matches/$MATCH_ID/overview/ | python -m json.tool
```

## 📝 Пример полного workflow

1. **Загрузили видео** → получили `video_id`
2. **Вызвали** `GET /api/analytics/videos/<video_id>/info/`
3. **Скопировали** `match_id` из ответа
4. **Проверили аналитику** `GET /api/analytics/matches/<match_id>/overview/`
5. **Если нужны игроки** → создали через админку или API
6. **Проверили профиль игрока** `GET /api/analytics/matches/<match_id>/players/<player_id>/profile/`

## ⚠️ Важно

- Если `match_id` = `null` → аналитика недоступна (нужно создать матч)
- Если `players` = `[]` → метрики игроков недоступны (нужно создать игроков)
- Если `events.total` = `0` → события не обнаружены (проверьте детекцию)
