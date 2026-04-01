# Руководство по интеграции Video Upload

## Что было добавлено

### 1. Backend API для загрузки видео

**Новые endpoints:**
- `POST /api/analytics/videos/upload/` - Загрузка видео файла
- `POST /api/analytics/videos/<video_id>/process/` - Запуск обработки
- `GET /api/analytics/videos/<video_id>/status/` - Статус обработки

**Новая модель:**
- `VideoUpload` - Хранит метаданные загруженных видео

### 2. Frontend компонент

**Новая страница:**
- `/upload` - Страница загрузки видео с формой

**Новый компонент:**
- `VideoUpload.tsx` - Компонент с drag & drop, прогресс-баром

### 3. Настройки Django

- Добавлен `MEDIA_ROOT` и `MEDIA_URL` для хранения файлов
- Модель зарегистрирована в admin панели

---

## Установка и настройка

### 1. Создать миграцию

```bash
cd backend
python manage.py makemigrations analytics
python manage.py migrate
```

### 2. Создать директорию для медиа файлов

```bash
mkdir -p backend/media/video_uploads
```

### 3. Обновить настройки (уже сделано)

В `backend/config/settings/base.py` уже добавлено:
```python
MEDIA_ROOT = BASE_DIR / "media"
MEDIA_URL = "/media/"
```

### 4. Настроить URL для медиа файлов (в development)

В `backend/config/urls.py` добавить:

```python
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # ... existing patterns
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

---

## Использование

### Через веб-интерфейс

1. Запустить frontend:
```bash
cd frontend
npm run dev
```

2. Запустить backend:
```bash
cd backend
python manage.py runserver
```

3. Открыть http://localhost:3000/upload

4. Загрузить видео файл, указать параметры (опционально)

5. Нажать "Upload & Process Video"

### Через API напрямую

```bash
# 1. Загрузить видео
curl -X POST http://127.0.0.1:8000/api/analytics/videos/upload/ \
  -F "file=@/path/to/video.mp4" \
  -F "period=2" \
  -F "video_start_offset_ms=3600000"

# Ответ: {"id": "uuid", "status": "uploaded", ...}

# 2. Запустить обработку
curl -X POST http://127.0.0.1:8000/api/analytics/videos/<video_id>/process/

# 3. Проверить статус
curl http://127.0.0.1:8000/api/analytics/videos/<video_id>/status/
```

---

## Важные замечания

### ⚠️ Текущая реализация

- **Синхронная обработка**: Обработка видео блокирует HTTP запрос
- **Нет очереди**: Нельзя обрабатывать несколько видео одновременно
- **Нет прогресса**: Нет real-time обновления статуса

### ✅ Рекомендации для production

1. **Добавить Celery** для асинхронной обработки:
   ```python
   # tasks.py
   @shared_task
   def process_video_task(video_upload_id):
       # ... processing logic
   ```

2. **Добавить WebSocket/SSE** для real-time обновлений статуса

3. **Добавить валидацию** размера файла на frontend

4. **Добавить chunked upload** для больших файлов

5. **Добавить обработку ошибок** и retry механизм

---

## Следующие шаги

1. ✅ Создать миграцию и применить
2. ✅ Протестировать загрузку через веб-интерфейс
3. ⏳ Добавить Celery для асинхронной обработки
4. ⏳ Добавить WebSocket для real-time статуса
5. ⏳ Улучшить обработку ошибок
