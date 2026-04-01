# Быстрое решение: Создать матч для уже загруженного видео

## 🎯 Ваша ситуация

Вы загрузили видео, но матч не был создан. Теперь можно создать матч для существующего видео!

## ✅ Решение 1: Через скрипт (САМЫЙ ПРОСТОЙ)

```bash
python create_match_for_video.py 1df04b30-f5f7-4566-a2da-f6071361bbd4 "Real Madrid" "Barcelona"
```

**Где:**
- `1df04b30-f5f7-4566-a2da-f6071361bbd4` - ваш Video ID
- `"Real Madrid"` - название первой команды
- `"Barcelona"` - название второй команды

## ✅ Решение 2: Через интерактивный скрипт

```bash
python check_analytics.py
```

Скрипт автоматически предложит создать матч, если его нет!

## ✅ Решение 3: Через API (curl)

```bash
curl -X POST http://127.0.0.1:8000/api/analytics/videos/1df04b30-f5f7-4566-a2da-f6071361bbd4/create-match/ \
  -H "Content-Type: application/json" \
  -d '{
    "team1_name": "Real Madrid",
    "team2_name": "Barcelona",
    "period": 2,
    "video_start_offset_ms": 3600000
  }'
```

## ✅ Решение 4: Через браузер (Postman/Insomnia)

1. Метод: `POST`
2. URL: `http://127.0.0.1:8000/api/analytics/videos/1df04b30-f5f7-4566-a2da-f6071361bbd4/create-match/`
3. Body (JSON):
```json
{
  "team1_name": "Real Madrid",
  "team2_name": "Barcelona",
  "period": 2,
  "video_start_offset_ms": 3600000
}
```

## 📋 Что произойдет

После создания матча:
1. ✅ Матч будет создан и связан с видео
2. ✅ Команды будут созданы автоматически
3. ✅ События из JSON будут экспортированы в БД (если видео уже обработано)
4. ✅ Аналитика станет доступна сразу!

## 🔍 Проверка после создания

```bash
# Проверить информацию о видео
python check_analytics.py

# Или через API
curl http://127.0.0.1:8000/api/analytics/videos/1df04b30-f5f7-4566-a2da-f6071361bbd4/info/
```

## 🚀 Быстрый старт

**Для вашего видео выполните:**

```bash
python create_match_for_video.py 1df04b30-f5f7-4566-a2da-f6071361bbd4 "Team 1" "Team 2"
```

Замените "Team 1" и "Team 2" на реальные названия команд!

После этого аналитика будет доступна по Match ID, который вернется в ответе.
