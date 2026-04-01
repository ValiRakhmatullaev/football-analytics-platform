# 📁 Архитектура хранения файлов

## 🎯 Принципы

1. **Единая точка входа**: Все пути через `MediaPaths` класс
2. **Предсказуемость**: Все файлы под `MEDIA_ROOT` с четкой структурой
3. **Масштабируемость**: Легко добавить новые типы файлов
4. **Без дублирования**: Один источник правды для путей

---

## 📂 Структура папок

```
media/
├── video_uploads/          # Загруженные видео
│   └── <uuid>.mp4
│
├── analytics/              # JSON результаты аналитики
│   └── <video_upload_id>/
│       └── <video_upload_id>_events.json
│
├── clips/                 # Видео клипы (highlights)
│   └── <video_upload_id>/
│       └── <clip_name>.mp4
│
└── thumbnails/            # Миниатюры клипов
    └── <video_upload_id>/
        └── <clip_name>_thumb.jpg
```

---

## 🔧 Использование

### В коде

```python
from apps.analytics.storage import MediaPaths

# Получить директорию для загрузок
uploads_dir = MediaPaths.get_video_uploads_dir()

# Получить директорию для JSON конкретного видео
analytics_dir = MediaPaths.get_analytics_output_dir(video_upload_id="uuid")

# Получить директорию для клипов
clips_dir = MediaPaths.get_video_clips_dir(video_upload_id="uuid")

# Создать все необходимые директории
MediaPaths.ensure_directories(video_upload_id="uuid")
```

---

## 📍 Пути в коде

### ✅ Правильно (использует MediaPaths)

```python
# backend/apps/analytics/api/video_upload.py
uploads_dir = MediaPaths.get_video_uploads_dir()
analytics_dir = MediaPaths.get_analytics_output_dir(video_upload_id=str(video_upload.id))
clips_dir = MediaPaths.get_video_clips_dir(video_upload_id=str(video_upload.id))
```

### ❌ Неправильно (старый способ)

```python
# НЕ ИСПОЛЬЗУЙТЕ:
Path(settings.MEDIA_ROOT) / "video_uploads"  # ❌
Path(settings.MEDIA_ROOT) / "analytics_output"  # ❌
self.video_path.parent / "analytics_output"  # ❌
```

---

## 🔄 Миграция со старой структуры

### Старая структура (удалить)

```
analytics_output/          # ❌ В корне проекта
├── debug/
└── <video_name>_events.json

media/
└── analytics_output/     # ❌ Старое название
    └── <video_upload_id>/
```

### Новая структура (использовать)

```
media/
├── analytics/            # ✅ Новое название
│   └── <video_upload_id>/
│       └── <video_upload_id>_events.json
├── clips/                # ✅ Отдельно от video_clips
└── thumbnails/           # ✅ Отдельно от clips
```

---

## 🛠️ Обновление существующих файлов

Если у вас есть старые файлы в `analytics_output/` в корне проекта:

1. **Не удаляйте их сразу** - они могут быть нужны
2. **Новые загрузки** будут использовать новую структуру
3. **Миграция** (опционально):
   ```bash
   # Найти старые JSON файлы
   find analytics_output -name "*_events.json"
   
   # Переместить в новую структуру (если нужно)
   # Но лучше оставить как есть - они не мешают
   ```

---

## 📝 Файлы, которые используют MediaPaths

- ✅ `backend/apps/analytics/api/video_upload.py` - загрузка и обработка
- ✅ `backend/apps/analytics/management/commands/create_clips.py` - создание клипов
- ✅ `backend/apps/analytics/services/video_clipper.py` - создание клипов (частично)

---

## 🚀 Преимущества новой архитектуры

1. **Нет дублирования**: Все пути в одном месте
2. **Легко изменить**: Меняете `MediaPaths` - меняется везде
3. **Предсказуемость**: Всегда знаете, где искать файлы
4. **Тестируемость**: Легко мокировать пути в тестах
5. **Документированность**: Структура понятна из кода

---

## ⚠️ Важно

- **Не создавайте папки вручную** - используйте `MediaPaths.ensure_directories()`
- **Не хардкодьте пути** - используйте `MediaPaths` методы
- **Всегда используйте абсолютные пути** - `MediaPaths` делает это автоматически

---

## 🔍 Проверка структуры

```python
# В Django shell
from apps.analytics.storage import MediaPaths
from pathlib import Path

# Проверить, что все директории существуют
media_root = MediaPaths.get_media_root()
print(f"MEDIA_ROOT: {media_root}")
print(f"Exists: {media_root.exists()}")

# Проверить структуру
for method in [MediaPaths.get_video_uploads_dir, 
               MediaPaths.get_analytics_output_dir,
               MediaPaths.get_video_clips_dir]:
    path = method()
    print(f"{method.__name__}: {path}")
    print(f"  Exists: {path.exists()}")
```
