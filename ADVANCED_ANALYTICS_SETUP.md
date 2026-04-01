# Настройка продвинутой аналитики с YOLOv8 + ByteTrack

## 📦 Установка зависимостей

### 1. Установите Ultralytics YOLO

```bash
pip install ultralytics
```

### 2. Установите ByteTrack

```bash
# Клонируйте репозиторий
git clone https://github.com/ifzhang/ByteTrack.git
cd ByteTrack
pip install -r requirements.txt
pip install -e .

# Или установите напрямую
pip install byte-track
```

### 3. Обновите requirements.txt

Добавьте в `backend/requirements.txt`:

```
ultralytics>=8.0.0
opencv-python>=4.8.0
numpy>=1.24.0
```

## 🔧 Что было реализовано

### 1. Advanced Detector (`video_analytics/advanced_detector.py`)

**Функционал:**
- Детекция игроков и мяча с помощью YOLOv8n
- Трекинг объектов с помощью ByteTrack
- Определение контроля мяча
- Fallback детекция мяча по цвету (если YOLO не находит)

**Использование:**
```python
from video_analytics.advanced_detector import AdvancedDetector

detector = AdvancedDetector()
detections, tracks = detector.detect_frame(frame, frame_id)
ball_control = detector.get_ball_control(tracks)
```

### 2. Advanced Event Detector (`video_analytics/event_detector_advanced.py`)

**Функционал:**
- Детекция передач (pass)
- Детекция ударов (shot)
- Детекция отборов (recovery)
- Детекция потерь (turnover)

**Использование:**
```python
from video_analytics.event_detector_advanced import AdvancedEventDetector

event_detector = AdvancedEventDetector()
events = event_detector.process_frame(
    frame_id, tracks, ball_control, teams, homography
)
```

### 3. Metrics Calculator (`video_analytics/metrics_calculator.py`)

**Командные метрики (7 штук):**
1. **Владение мячом (Possession)** - процент времени владения
2. **Общее количество ударов (Total shots)** - счетчик
3. **Удары в створ (Shots on target)** - удары, попавшие в створ
4. **Количество передач (Passes)** - общее количество
5. **Процент успешных передач (Pass accuracy)** - успешные / всего
6. **Количество отборов (Recoveries)** - в средней и атакующей трети
7. **Количество потерь (Turnovers)** - в своей трети

**Игровые метрики (4 штуки):**
1. **Активность (Activity index)** - нормализованное пройденное расстояние
2. **Пас (Pass score)** - (вперед - назад) / всего передач
3. **Устойчивость к прессингу (Pressure resistance)** - 1 - (потери под прессингом / касания)
4. **Доминирование в зоне (Zone dominance)** - процент касаний в атакующей трети

### 4. Advanced Metrics Service (`backend/apps/analytics/services/advanced_metrics.py`)

Сервис для расчета метрик из данных БД и видео.

### 5. UI Компоненты

**TeamMetricsCard** - отображение командных метрик
**PlayerMetricsCard** - отображение игровых метрик

## 🚀 Интеграция в пайплайн

### Обновленный пайплайн обработки видео:

```python
from video_analytics.advanced_detector import AdvancedDetector
from video_analytics.event_detector_advanced import AdvancedEventDetector
from video_analytics.metrics_calculator import MetricsCalculator

# 1. Инициализация
detector = AdvancedDetector()
event_detector = AdvancedEventDetector()
metrics_calculator = MetricsCalculator()

# 2. Обработка каждого кадра
for frame_id, frame in enumerate(video_frames):
    # Детекция и трекинг
    detections, tracks = detector.detect_frame(frame, frame_id)
    
    # Определение контроля мяча
    ball_control = detector.get_ball_control(tracks)
    
    # Детекция событий
    events = event_detector.process_frame(
        frame_id, tracks, ball_control, teams, homography
    )
    
    # Сохранение данных для расчета метрик
    # ...

# 3. Расчет метрик
team_metrics = metrics_calculator.calculate_team_metrics(...)
player_metrics = metrics_calculator.calculate_player_metrics(...)
```

## 📊 Страница аналитики игрока

Страница `/matches/[matchId]/players/[playerId]` теперь показывает:

1. **Командные метрики** - 7 метрик в виде карточек
2. **Игровые метрики** - 4 метрики с цветовой индикацией
3. Существующие метрики (Performance, Trends, Insights)

## 🔄 Следующие шаги

1. **Интегрировать в pipeline.py:**
   - Заменить простой детектор на AdvancedDetector
   - Использовать AdvancedEventDetector
   - Сохранять tracking данные

2. **Улучшить детекцию команд:**
   - Автоматическое определение команд по цвету формы
   - Или ручное назначение в начале матча

3. **Калибровка поля:**
   - Автоматическая калибровка с помощью детекции линий
   - Или ручная калибровка по углам

4. **Сохранение tracking данных:**
   - Создать модель для хранения tracking данных
   - Сохранять позиции игроков и мяча по кадрам

## ⚠️ Примечания

- YOLOv8n загружается автоматически при первом использовании
- ByteTrack требует дополнительной настройки
- Для MVP можно использовать упрощенный трекинг без ByteTrack
- Метрики рассчитываются из событий в БД (fallback режим)

## 📝 API Endpoints

### Получить метрики игрока:
```
GET /api/analytics/matches/{match_id}/players/{player_id}/profile/
```

Ответ включает:
- `team_metrics` - командные метрики
- `player_metrics` - игровые метрики
