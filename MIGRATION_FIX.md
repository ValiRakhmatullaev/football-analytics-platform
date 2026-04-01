# Исправление проблем с миграциями

## ✅ Текущий статус

Миграция `0001_video_upload` уже применена к базе данных.

## 🔍 Проверка миграций

Если вы получили ошибку "The string did not match the expected pattern", это может быть из-за:

1. **Проблема с форматом миграции** - уже исправлено
2. **Конфликт миграций** - нужно проверить
3. **Проблема с зависимостями** - нужно проверить

## 📋 Инструкция по применению миграций

### Если миграция НЕ применена:

```bash
cd backend
python manage.py makemigrations analytics
python manage.py migrate analytics
```

### Если миграция уже применена (как сейчас):

Ничего делать не нужно! Миграция уже применена.

### Если нужно пересоздать миграцию:

```bash
cd backend

# 1. Удалить старую миграцию (ОСТОРОЖНО - только если не в production!)
# rm apps/analytics/migrations/0001_video_upload.py

# 2. Создать новую
python manage.py makemigrations analytics

# 3. Применить
python manage.py migrate analytics
```

## 🔧 Проверка состояния

### Проверить статус миграций:
```bash
python manage.py showmigrations analytics
```

Должно показать:
```
analytics
 [X] 0001_video_upload  # [X] означает применено
```

### Проверить модель в БД:
```bash
python manage.py shell
```

```python
from apps.analytics.models import VideoUpload
# Если импорт работает - модель правильная
VideoUpload._meta.get_fields()  # Проверить поля
```

## ⚠️ Если ошибка все еще есть

### Вариант 1: Проблема с полем json_output_path

Если поле `json_output_path` не существует в БД, создайте новую миграцию:

```bash
python manage.py makemigrations analytics
python manage.py migrate analytics
```

### Вариант 2: Проблема с зависимостями

Проверьте, что все зависимости применены:

```bash
python manage.py migrate
```

### Вариант 3: Сброс миграций (ТОЛЬКО для разработки!)

```bash
# ОСТОРОЖНО: Это удалит все данные!
python manage.py migrate analytics zero
python manage.py migrate analytics
```

## ✅ Быстрая проверка

Выполните эти команды для проверки:

```bash
cd backend

# 1. Проверить миграции
python manage.py showmigrations analytics

# 2. Проверить код
python manage.py check

# 3. Проверить модель
python manage.py shell -c "from apps.analytics.models import VideoUpload; print(VideoUpload._meta.get_fields())"
```

## 📝 Текущее состояние

✅ Миграция `0001_video_upload` применена
✅ Модель `VideoUpload` должна работать
✅ Поле `json_output_path` добавлено в миграцию

Если вы получили ошибку при работе с кодом (не при миграции), возможно проблема в другом месте. Покажите полный текст ошибки для диагностики.
