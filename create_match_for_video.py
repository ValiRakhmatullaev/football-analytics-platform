#!/usr/bin/env python3
"""
Скрипт для создания матча для уже загруженного видео.
Использование: python create_match_for_video.py <video_id> <team1_name> <team2_name>
"""

import requests
import json
import sys

BASE_URL = "http://127.0.0.1:8000"


def main():
    if len(sys.argv) < 4:
        print("Использование: python create_match_for_video.py <video_id> <team1_name> <team2_name>")
        print("\nПример:")
        print("  python create_match_for_video.py 1df04b30-f5f7-4566-a2da-f6071361bbd4 'Real Madrid' 'Barcelona'")
        sys.exit(1)
    
    video_id = sys.argv[1]
    team1_name = sys.argv[2]
    team2_name = sys.argv[3]
    
    print("=" * 70)
    print("Создание матча для видео")
    print("=" * 70)
    print(f"Video ID: {video_id}")
    print(f"Team 1: {team1_name}")
    print(f"Team 2: {team2_name}")
    print()
    
    # Создать матч
    print("Создаю матч...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/analytics/videos/{video_id}/create-match/",
            json={
                "team1_name": team1_name,
                "team2_name": team2_name,
                "period": 2,
                "video_start_offset_ms": 3600000
            }
        )
        response.raise_for_status()
        data = response.json()
        
        print("✅ Матч создан успешно!")
        print()
        print(f"Match ID: {data['match_id']}")
        print(f"Team 1 ID: {data['team1']['id']}")
        print(f"Team 2 ID: {data['team2']['id']}")
        print()
        print(f"📊 Аналитика доступна:")
        print(f"   {BASE_URL}{data['analytics_url']}")
        print()
        print("✅ События экспортированы в БД (если были обработаны)")
        
    except requests.exceptions.ConnectionError:
        print("❌ Ошибка: Не могу подключиться к серверу.")
        print("   Убедитесь, что Django сервер запущен: python manage.py runserver")
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        error_data = e.response.json() if e.response.content else {}
        print(f"❌ Ошибка: {error_data.get('detail', error_data.get('error', str(e)))}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
