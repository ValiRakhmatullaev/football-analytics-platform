# Исправления проблем с клипами

## ✅ Исправлено

### 1. Ошибка "EmptyRanges" на фронтенде
- Добавлена обработка ошибок для видео элемента
- Добавлены обработчики `onError`, `onLoadStart`, `onCanPlay`
- Улучшены сообщения об ошибках с детализацией типа ошибки
- Убрано `crossOrigin="anonymous"` (может вызывать проблемы с CORS)

### 2. Создание только одной нарезки
- Улучшена обработка ошибок в `create_clips_from_events`
- Теперь если один клип не создался, процесс продолжается
- Добавлено логирование успешных и неудачных попыток
- Исправлены отступы в коде сохранения клипов в БД

### 3. Улучшена обработка ошибок
- Каждый клип обрабатывается в try/except
- Ошибки логируются, но не прерывают процесс
- Добавлена валидация файлов перед открытием

## 🔍 Диагностика

### Проверить логи Django
```bash
cd backend
python manage.py runserver
# Смотрите логи при обработке видео
```

### Проверить созданные клипы
```bash
# В Django shell
python manage.py shell
>>> from apps.analytics.models import VideoClip, VideoUpload
>>> video = VideoUpload.objects.first()
>>> clips = VideoClip.objects.filter(video_upload=video)
>>> print(f"Всего клипов: {clips.count()}")
>>> for clip in clips:
...     print(f"{clip.title}: {clip.file_path} - exists: {Path(clip.file_path).exists()}")
```

### Проверить файлы клипов
```bash
ls -la backend/media/video_clips/<video_id>/
```

## 🛠️ Если клипы все еще не создаются

1. **Проверьте события**:
   - Должно быть > 0 событий в JSON
   - События должны иметь достаточный confidence

2. **Проверьте FFmpeg**:
   ```bash
   /Users/valijonrakhmatullaev/PyCharmMiscProject/ffmpeg_bin/ffmpeg -version
   ```

3. **Проверьте права доступа**:
   ```bash
   ls -la backend/media/video_clips/
   chmod -R 755 backend/media/
   ```

4. **Создайте клипы вручную**:
   ```bash
   python manage.py create_clips <video_id>
   ```

## 📝 Что изменилось

### Backend (`video_clipper.py`)
- Добавлен try/except для каждого клипа
- Улучшено логирование
- Процесс не останавливается при ошибке одного клипа

### Backend (`video_upload.py`)
- Исправлены отступы
- Добавлен try/except при сохранении в БД
- Улучшена обработка ошибок

### Frontend (`VideoClipsViewer.tsx`)
- Добавлена обработка ошибок видео
- Улучшены сообщения об ошибках
- Добавлено состояние `videoError`

### Backend (`video_clips.py`)
- Улучшена обработка ошибок при открытии файлов
