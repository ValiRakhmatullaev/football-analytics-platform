# Настройка аналитики после обработки видео

## ✅ Что было улучшено

### 1. Автоматическое создание матча
- ✅ Добавлена опция "Create match automatically" в форму загрузки
- ✅ При создании автоматически создаются команды и связываются с матчем
- ✅ События автоматически сохраняются в БД и доступны для аналитики

### 2. Улучшенная обработка видео
- ✅ События всегда сохраняются в JSON
- ✅ События сохраняются в БД если есть match_id
- ✅ Возвращается информация о доступности аналитики

### 3. Интеграция с аналитикой
- ✅ После обработки можно сразу использовать API аналитики
- ✅ Статус показывает доступность аналитики
- ✅ Возвращается ссылка на аналитику матча

## 🎯 Как использовать

### Вариант 1: Автоматическое создание матча (РЕКОМЕНДУЕТСЯ)

1. Загрузите видео через `/upload`
2. Отметьте "Create match automatically"
3. Введите названия команд (Team 1 и Team 2)
4. Загрузите и обработайте видео
5. После обработки аналитика будет доступна автоматически!

### Вариант 2: Использование существующего матча

1. Загрузите видео через `/upload`
2. Укажите существующий `match_id`
3. Загрузите и обработайте видео
4. События будут добавлены к существующему матчу

## 📊 Доступные API аналитики

После обработки видео с созданным матчем доступны:

### 1. Обзор матча
```
GET /api/analytics/matches/<match_id>/overview/
```
Возвращает:
- Метрики команд (possession, turnovers, EPI)
- Список игроков
- Темп матча

### 2. Профиль игрока
```
GET /api/analytics/matches/<match_id>/players/<player_id>/profile/
```
Возвращает:
- Детальную аналитику игрока
- События по типам
- Метрики по позиции
- Timeline событий

### 3. Тренерская аналитика
```
GET /api/analytics/coach-summary/?team_id=<team_id>&match_ids[]=<match_id>
```
Возвращает:
- Сильные стороны
- Слабые стороны
- Тактические инсайты
- Нагрузка игроков

## 🔍 Проверка работы аналитики

### После обработки видео:

1. **Проверить статус:**
   ```bash
   GET /api/analytics/videos/<video_id>/status/
   ```
   Должно показать `"analytics_available": true`

2. **Проверить события в БД:**
   ```python
   from apps.events.models import Event
   from apps.competitions.models import Match
   
   match = Match.objects.get(id="<match_id>")
   events = Event.objects.filter(match=match)
   print(f"Events count: {events.count()}")
   ```

3. **Проверить аналитику:**
   ```bash
   GET /api/analytics/matches/<match_id>/overview/
   ```
   Должны быть метрики команд и игроков

## ⚠️ Важные замечания

### Для работы аналитики нужно:

1. ✅ **События в БД** - сохраняются автоматически при обработке
2. ✅ **Матч с командами** - создается автоматически или указывается
3. ⚠️ **Игроки с Appearances** - нужно создать вручную или через админку

### Создание игроков и Appearances:

```python
from apps.players.models import Player, Appearance
from apps.competitions.models import Match
from apps.teams.models import Team

# Создать игрока
player = Player.objects.create(
    first_name="John",
    last_name="Doe",
    primary_position="MF"
)

# Создать Appearance (участие в матче)
match = Match.objects.get(id="<match_id>")
team = Team.objects.get(id="<team_id>")

Appearance.objects.create(
    player=player,
    match=match,
    team=team,
    minutes_played=90,
    started=True
)
```

## 🚀 Быстрый старт

1. **Загрузите видео** с автоматическим созданием матча
2. **Дождитесь обработки** (может занять несколько минут)
3. **Создайте игроков** через админку Django или API
4. **Проверьте аналитику** через API endpoints

## 📝 Пример использования

```bash
# 1. Загрузить видео (создать матч автоматически)
POST /api/analytics/videos/upload/
{
  "file": <video_file>,
  "create_match": true,
  "team1_name": "Real Madrid",
  "team2_name": "Barcelona",
  "period": 2
}

# 2. Обработать видео
POST /api/analytics/videos/<video_id>/process/

# 3. Проверить аналитику
GET /api/analytics/matches/<match_id>/overview/
```

## ✅ Результат

После этих шагов аналитика будет работать полностью:
- ✅ Метрики команд
- ✅ Метрики игроков
- ✅ Тренерская аналитика
- ✅ Все API endpoints доступны
