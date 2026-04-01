# Отладка проблемы с созданием клипов

## 🔍 Диагностика проблемы

### 1. Проверить миграцию

```bash
cd backend
python manage.py showmigrations analytics
```

Должно быть:
```
[X] 0003_video_clip
```

Если нет - применить:
```bash
python manage.py migrate analytics
```

### 2. Проверить события

Если событий 0, клипы не создадутся. Проверьте:
- Детекция событий работает?
- Есть ли события в JSON файле?

### 3. Проверить FFmpeg

```bash
# Проверить доступность
which ffmpeg
# или
/Users/valijonrakhmatullaev/PyCharmMiscProject/ffmpeg_bin/ffmpeg -version
```

### 4. Проверить логи

При обработке видео проверьте логи Django - там будут ошибки создания клипов.

## 🛠️ Решения

### Решение 1: Создать клипы вручную

Если видео уже обработано, но клипы не созданы:

```bash
cd backend
python manage.py create_clips <video_id>
```

### Решение 2: Настроить FFmpeg путь

Добавьте в `backend/config/settings/base.py`:

```python
FFMPEG_PATH = "/Users/valijonrakhmatullaev/PyCharmMiscProject/ffmpeg_bin/ffmpeg"
```

### Решение 3: Проверить события

Если событий 0:
- Улучшите детекцию (уже сделано ранее)
- Попробуйте загрузить видео снова
- Проверьте качество видео

## 📋 Чеклист

- [ ] Миграция применена
- [ ] FFmpeg доступен
- [ ] События обнаружены (> 0)
- [ ] JSON файл существует
- [ ] Видео файл существует
- [ ] Права на запись в media/video_clips/

## 🔧 Команда для создания клипов

```bash
# Получить video_id из списка видео
python check_analytics.py

# Создать клипы
cd backend
python manage.py create_clips <video_id>
```

## ⚠️ Исправление ошибки UUID

Ошибка в coach-summary исправлена - теперь валидируются UUID и фильтруются пустые значения.
