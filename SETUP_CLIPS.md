# Настройка системы нарезки видео

## ✅ Что реализовано

1. **Автоматическая нарезка** - при обработке видео создаются клипы с важными моментами
2. **Модель VideoClip** - хранит информацию о каждом клипе
3. **API endpoints** - для получения и просмотра клипов
4. **UI компонент** - для просмотра клипов в браузере

## 🚀 Быстрый старт

### 1. Применить миграцию

```bash
cd backend
python manage.py migrate analytics
```

### 2. Настроить FFmpeg (если нужно)

Если ffmpeg не в PATH, добавьте в `backend/config/settings/base.py`:

```python
FFMPEG_PATH = "/Users/valijonrakhmatullaev/PyCharmMiscProject/ffmpeg_bin/ffmpeg"
```

### 3. Загрузить видео

1. Откройте `/upload`
2. Загрузите видео с "Create match automatically"
3. Дождитесь обработки
4. Клипы создадутся автоматически!

### 4. Просмотреть клипы

После обработки:
- Нажмите "🎬 Просмотреть клипы" в форме загрузки
- Или откройте: `/videos/<video_id>/clips`

## 📋 Типы клипов

Система автоматически создает клипы для:

- **Голы** (goal) - удары с высокой уверенностью (>0.7)
- **Удары** (shot) - удары по воротам (>0.5)
- **Опасные моменты** (dangerous_moment) - удары/пасы (>0.4)
- **Ключевые пасы** (pass) - важные пасы (>0.6)

## 🎬 Как это работает

1. **Обработка видео** → детекция событий
2. **Определение важных моментов** → фильтрация по типу и уверенности
3. **Обрезка видео** → ffmpeg создает клипы с контекстом
4. **Генерация миниатюр** → создается thumbnail для каждого клипа
5. **Сохранение в БД** → информация о клипах сохраняется

## 📁 Структура файлов

```
backend/media/
  video_uploads/
    <video_id>.mp4
  video_clips/
    <video_id>/
      <video_id>_clip_001_goal.mp4
      <video_id>_clip_001_goal_thumb.jpg
      <video_id>_clip_002_shot.mp4
      ...
```

## 🔧 Настройка

### Длительность клипов

В `backend/apps/analytics/services/video_clipper.py`:

```python
clip_config = {
    "type": "goal",
    "start_offset": -5.0,  # 5 секунд до события
    "end_offset": 10.0,     # 10 секунд после
}
```

### Пороги уверенности

```python
# Голы
if event_type == "shot" and confidence > 0.7:  # Изменить порог

# Удары
elif event_type == "shot" and confidence > 0.5:  # Изменить порог
```

### Качество клипов

```python
clipper.clip_video(
    ...,
    quality="medium"  # "low", "medium", "high"
)
```

## 📊 API Endpoints

### Получить все клипы
```bash
GET /api/analytics/videos/<video_id>/clips/
```

### Фильтр по типу
```bash
GET /api/analytics/videos/<video_id>/clips/?type=goal
```

### Просмотр видео
```bash
GET /api/analytics/clips/<clip_id>/video/
```

### Миниатюра
```bash
GET /api/analytics/clips/<clip_id>/thumbnail/
```

## 🎨 UI Компоненты

### VideoClipsViewer
- Отображает сетку клипов с миниатюрами
- Фильтрация по типам
- Встроенный видеоплеер
- Информация о каждом клипе

### Страница просмотра
- `/videos/[videoId]/clips` - полная страница с клипами

## ⚠️ Важно

1. **FFmpeg обязателен** - без него клипы не создадутся
2. **Обработка может занять время** - зависит от количества событий
3. **Клипы занимают место на диске** - следите за размером
4. **Клипы создаются только для важных моментов** - с достаточной уверенностью

## 🐛 Troubleshooting

### Клипы не создаются

1. Проверить ffmpeg:
   ```bash
   which ffmpeg
   # или
   /Users/valijonrakhmatullaev/PyCharmMiscProject/ffmpeg_bin/ffmpeg -version
   ```

2. Проверить логи Django - ошибки будут в консоли

3. Проверить события - если событий 0, клипов не будет

### Ошибка "ffmpeg not found"

Добавьте в `settings/base.py`:
```python
FFMPEG_PATH = "/Users/valijonrakhmatullaev/PyCharmMiscProject/ffmpeg_bin/ffmpeg"
```

### Клипы создаются, но не отображаются

1. Проверить MEDIA_URL в settings
2. Проверить права доступа к файлам
3. Проверить, что файлы существуют

## ✅ Готово к использованию!

После применения миграции система готова:
- Загрузите видео
- Дождитесь обработки
- Просмотрите клипы!
