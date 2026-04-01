# 📁 Где сохраняются данные после загрузки видео

## 🎯 Краткий ответ

После загрузки видео данные сохраняются в **3 местах**:

1. **Видео файл** → `media/video_uploads/<uuid>.mp4`
2. **Метаданные** → База данных (таблица `video_uploads`)
3. **Результаты обработки** → JSON файл в `analytics_output/` + события в БД

---

## 📂 Детальное описание

### 1. **Видео файл** (физический файл)

**Где сохраняется:**
```
<PROJECT_ROOT>/media/video_uploads/<uuid>.mp4
```

**Пример:**
```
/Users/valijonrakhmatullaev/PycharmProjects/football-analytics-platform/media/video_uploads/8999ae63-f460-45e8-b537-12e2be4fe275.mp4
```

**Код:**
```python
# backend/apps/analytics/api/video_upload.py, строка 129-140
uploads_dir = Path(settings.MEDIA_ROOT) / "video_uploads"
uploads_dir.mkdir(parents=True, exist_ok=True)

file_id = uuid.uuid4()
file_name = f"{file_id}{file_ext}"
file_path = uploads_dir / file_name

# Сохранение файла
with open(file_path, 'wb+') as destination:
    for chunk in video_file.chunks():
        destination.write(chunk)
```

**Настройка:**
- `MEDIA_ROOT` определяется в `backend/config/settings/base.py`:
  ```python
  MEDIA_ROOT = BASE_DIR / "media"
  ```

---

### 2. **Метаданные видео** (база данных)

**Где сохраняется:**
- Таблица: `video_uploads` в SQLite (или PostgreSQL в production)
- Файл БД: `<PROJECT_ROOT>/config/db.sqlite3`

**Что сохраняется:**
```python
# backend/apps/analytics/models.py
class VideoUpload(models.Model):
    id = UUIDField()                    # Уникальный ID
    file_name = CharField()             # Оригинальное имя файла
    file_path = CharField()             # Путь к файлу на диске
    file_size = BigIntegerField()       # Размер в байтах
    duration_seconds = FloatField()     # Длительность (после обработки)
    width = IntegerField()              # Ширина (после обработки)
    height = IntegerField()             # Высота (после обработки)
    fps = FloatField()                  # FPS (после обработки)
    status = CharField()                # uploaded/processing/completed/failed
    match = ForeignKey()                # Связь с матчем (если указан)
    period = PositiveSmallIntegerField() # Период (1 или 2)
    video_start_offset_ms = IntegerField() # Смещение начала
    events_count = IntegerField()       # Количество событий
    json_output_path = CharField()      # Путь к JSON файлу
    processing_error = TextField()      # Ошибка (если была)
    uploaded_at = DateTimeField()       # Время загрузки
    processed_at = DateTimeField()      # Время обработки
```

**Код создания записи:**
```python
# backend/apps/analytics/api/video_upload.py, строка 143-151
video_upload = VideoUpload.objects.create(
    file_name=video_file.name,
    file_path=str(file_path),
    file_size=video_file.size,
    status=VideoUpload.Status.UPLOADED,
    match=match,
    period=int(period) if period else None,
    video_start_offset_ms=video_start_offset_ms,
)
```

**Как посмотреть:**
```bash
# Django shell
python manage.py shell

>>> from apps.analytics.models import VideoUpload
>>> videos = VideoUpload.objects.all()
>>> for v in videos:
...     print(f"{v.file_name} - {v.status} - {v.events_count} events")
```

---

### 3. **Результаты обработки** (JSON файл + события в БД)

#### A. JSON файл (ВСЕГДА создается)

**Где сохраняется:**
```
<MEDIA_ROOT>/analytics_output/<video_upload_id>/<stem>_events.json
```
(Раньше был рядом с видео; теперь — в `media/analytics_output/<id>/` для предсказуемого пути.)

**Пример:**
```
.../backend/config/media/analytics_output/8999ae63-f460-45e8-b537-12e2be4fe275/8999ae63-f460-45e8-b537-12e2be4fe275_events.json
```

**Код:**
```python
# video_analytics/pipeline.py, строка 54
self.output_dir = Path(output_dir) if output_dir else self.video_path.parent / "analytics_output"

# video_analytics/pipeline.py, строка 159
self.exporter.export_to_json(
    self.detected_events,
    str(output_path),
    metadata=metadata
)
```

**Структура JSON:**
```json
{
  "metadata": {
    "video_path": "...",
    "match_id": "...",
    "period": 2,
    "video_start_offset_ms": 3600000,
    "events_count": 15,
    "processing_time_seconds": 45.2,
    "video_metadata": {
      "duration_seconds": 600.0,
      "width": 854,
      "height": 480,
      "fps": 25.0
    }
  },
  "events": [
    {
      "event_type": "pass",
      "timestamp_ms": 3605000,
      "x": 50.5,
      "y": 30.2,
      "confidence": 0.85,
      ...
    },
    ...
  ]
}
```

**Путь сохраняется в БД:**
```python
# backend/apps/analytics/api/video_upload.py, строка 212-214
json_output_path = result.get("output_file")
if json_output_path:
    video_upload.json_output_path = json_output_path
```

---

#### B. События в базе данных (УСЛОВНО)

**Где сохраняется:**
- Таблица: `events` в SQLite
- **Только если** при загрузке был указан `match_id`

**Код:**
```python
# backend/apps/analytics/api/video_upload.py, строка 216-221
if video_upload.match:
    try:
        pipeline.export_to_django()
        events_saved_to_db = True
    except Exception as e:
        logger.error(f"Failed to export events to DB: {e}")
```

**Что сохраняется:**
```python
# apps/events/models.py
class Event(models.Model):
    match = ForeignKey(Match)
    event_type = CharField()  # pass, shot, turnover, recovery, etc.
    timestamp_ms = IntegerField()
    x = FloatField()  # Координата X (0-100)
    y = FloatField()  # Координата Y (0-100)
    confidence = FloatField()
    period = IntegerField()
    ...
```

**Как посмотреть:**
```bash
python manage.py shell

>>> from apps.events.models import Event
>>> events = Event.objects.filter(match_id="...")
>>> for e in events:
...     print(f"{e.event_type} @ {e.timestamp_ms}ms - confidence: {e.confidence}")
```

---

### 4. **Видео клипы** (если создаются)

**Где сохраняются:**
```
<PROJECT_ROOT>/media/video_clips/<video_upload_id>/<clip_id>.mp4
```

**Пример:**
```
/Users/valijonrakhmatullaev/PycharmProjects/football-analytics-platform/media/video_clips/8999ae63-f460-45e8-b537-12e2be4fe275/clip_goal_123.mp4
```

**Код:**
```python
# backend/apps/analytics/api/video_upload.py, строка 253
clips_dir = Path(settings.MEDIA_ROOT) / "video_clips" / str(video_upload.id)
clips_dir.mkdir(parents=True, exist_ok=True)
```

**Метаданные клипов:**
- Таблица: `video_clips` в БД
- Связь с `VideoUpload` и `Event`

---

## 🔍 Как найти данные конкретного видео

### По ID видео:

```python
from apps.analytics.models import VideoUpload

video = VideoUpload.objects.get(id="8999ae63-f460-45e8-b537-12e2be4fe275")

# Путь к видео файлу
print(video.file_path)
# /path/to/media/video_uploads/8999ae63-f460-45e8-b537-12e2be4fe275.mp4

# Путь к JSON файлу
print(video.json_output_path)
# /path/to/analytics_output/second_half_60-70_events.json

# События в БД (если есть match)
if video.match:
    events = video.match.events.all()
    print(f"Events in DB: {events.count()}")
```

### По имени файла:

```python
video = VideoUpload.objects.get(file_name="second_half_60-70.mp4")
```

---

## 📊 Схема сохранения данных

```
Загрузка видео
    │
    ├─→ 1. Файл на диск
    │      media/video_uploads/<uuid>.mp4
    │
    ├─→ 2. Метаданные в БД
    │      video_uploads таблица
    │
    └─→ Обработка видео
            │
            ├─→ 3a. JSON файл (ВСЕГДА)
            │      analytics_output/<name>_events.json
            │      Сохраняется в video_uploads.json_output_path
            │
            ├─→ 3b. События в БД (если есть match_id)
            │      events таблица
            │
            └─→ 4. Видео клипы (если создаются)
                  media/video_clips/<video_id>/<clip>.mp4
                  video_clips таблица
```

---

## 🛠️ Полезные команды

### Посмотреть все загруженные видео:
```bash
python manage.py shell

>>> from apps.analytics.models import VideoUpload
>>> for v in VideoUpload.objects.all():
...     print(f"{v.id} | {v.file_name} | {v.status} | {v.events_count} events")
```

### Проверить, где находится JSON файл:
```bash
python manage.py shell

>>> from apps.analytics.models import VideoUpload
>>> video = VideoUpload.objects.first()
>>> print(f"JSON path: {video.json_output_path}")
>>> import os
>>> print(f"Exists: {os.path.exists(video.json_output_path)}")
```

### Посмотреть события из JSON:
```python
import json
from apps.analytics.models import VideoUpload

video = VideoUpload.objects.first()
if video.json_output_path:
    with open(video.json_output_path, 'r') as f:
        data = json.load(f)
        print(f"Events: {len(data['events'])}")
        print(f"First event: {data['events'][0] if data['events'] else 'None'}")
```

### Найти все файлы в media:
```bash
# В терминале
find media/ -type f -name "*.mp4"
find media/ -type f -name "*.json"
```

---

## ⚠️ Важные замечания

1. **JSON файл создается ВСЕГДА** - даже если обработка не удалась, JSON будет с пустым массивом событий
2. **События в БД создаются ТОЛЬКО если указан match_id** при загрузке
3. **Видео клипы создаются автоматически** после успешной обработки (если найдены события)
4. **Все пути относительные к PROJECT_ROOT** - проверьте `BASE_DIR` в settings

---

## 🔧 Настройка путей

Если нужно изменить места сохранения:

### Изменить папку для видео:
```python
# backend/config/settings/base.py
MEDIA_ROOT = BASE_DIR / "custom_media_folder"
```

### Изменить папку для JSON:
```python
# video_analytics/pipeline.py, строка 54
self.output_dir = Path("/custom/path/to/output")
```

---

## 📝 Резюме

| Тип данных | Где сохраняется | Когда создается |
|------------|----------------|----------------|
| Видео файл | `media/video_uploads/` | При загрузке |
| Метаданные | БД (`video_uploads`) | При загрузке |
| JSON с событиями | `analytics_output/` | После обработки (ВСЕГДА) |
| События в БД | БД (`events`) | После обработки (если есть match_id) |
| Видео клипы | `media/video_clips/` | После обработки (если найдены события) |
