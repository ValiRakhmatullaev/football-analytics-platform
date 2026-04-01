# Запуск backend и миграции

## Важно: откуда запускать

**Сервер и миграции нужно запускать из папки `backend/`.**

- В проекте есть два каталога с настройками: корень (`config/`) и `backend/config/`.
- API аналитики и таблицы `video_uploads` / `video_clips` есть только при запуске из **backend**.
- База данных при этом: `backend/config/db.sqlite3`.

Если запускать из **корня проекта** (`python manage.py runserver`), используется другая БД (`config/db.sqlite3`) и другая структура приложений, и возникает ошибка **no such table: video_uploads**.

---

## Что сделано

1. **Миграция 0002** сделана пустой (no-op), так как поле `json_output_path` уже есть в 0001.
2. **Миграции применены** к базе в `backend/`:
   - `analytics.0001_video_upload` — таблица `video_uploads`
   - `analytics.0002_add_json_output_path` — no-op
   - `analytics.0003_video_clip` — таблица `video_clips`
   - остальные приложения (auth, sessions и т.д.)

---

## Как запускать

```bash
# 1. Активировать виртуальное окружение (из корня проекта)
source .venv/bin/activate   # или: .venv\Scripts\activate на Windows

# 2. Перейти в backend
cd backend

# 3. При необходимости применить миграции
python manage.py migrate

# 4. Запустить сервер
python manage.py runserver
```

Или одной командой из корня проекта:

```bash
cd backend && ../.venv/bin/python manage.py runserver
```

---

## Если снова появится «no such table»

Убедитесь, что:

1. Запускаете сервер из каталога **backend/** (`cd backend` затем `python manage.py runserver`).
2. Миграции применены для этой же базы:  
   `cd backend && python manage.py migrate`
3. В настройках используется база `backend/config/db.sqlite3` (при запуске из `backend/` так и будет).

После этого загрузка видео и работа с `video_uploads` должны идти без этой ошибки.
