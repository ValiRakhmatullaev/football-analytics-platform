#!/usr/bin/env python3
"""
Скрипт для проверки аналитики после загрузки видео.
Показывает все необходимые ID и проверяет доступность аналитики.
"""

import requests
import json
import sys

BASE_URL = "http://127.0.0.1:8000"


def print_section(title):
    """Печатает заголовок секции."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def main():
    print_section("Проверка аналитики после загрузки видео")
    
    # 1. Получить список видео
    print("\n1. Получаю список загруженных видео...")
    try:
        response = requests.get(f"{BASE_URL}/api/analytics/videos/")
        response.raise_for_status()
        data = response.json()
        videos = data.get("videos", [])
    except requests.exceptions.ConnectionError:
        print("❌ Ошибка: Не могу подключиться к серверу.")
        print("   Убедитесь, что Django сервер запущен: python manage.py runserver")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        sys.exit(1)
    
    if not videos:
        print("⚠️  Нет загруженных видео.")
        print("   Загрузите видео через веб-интерфейс: http://127.0.0.1:3000/upload")
        sys.exit(0)
    
    # Показать список видео
    print(f"\n✅ Найдено видео: {len(videos)}")
    for i, video in enumerate(videos[:5], 1):  # Показать первые 5
        status_icon = "✅" if video["status"] == "completed" else "⏳"
        print(f"   {i}. {status_icon} {video['file_name']}")
        print(f"      ID: {video['id']}")
        print(f"      Статус: {video['status']}")
        print(f"      Событий: {video['events_count']}")
        if video.get("match_id"):
            print(f"      Match ID: {video['match_id']}")
        print()
    
    # Выбрать последнее завершенное видео
    completed_videos = [v for v in videos if v["status"] == "completed"]
    if not completed_videos:
        print("⚠️  Нет завершенных видео. Дождитесь обработки.")
        sys.exit(0)
    
    video = completed_videos[0]
    video_id = video["id"]
    match_id = video.get("match_id")
    
    print_section(f"Детальная информация о видео: {video['file_name']}")
    
    # 2. Получить детальную информацию
    print(f"\n2. Получаю детальную информацию (Video ID: {video_id})...")
    try:
        info_response = requests.get(f"{BASE_URL}/api/analytics/videos/{video_id}/info/")
        info_response.raise_for_status()
        info = info_response.json()
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        sys.exit(1)
    
    # Показать информацию о матче
    if info.get("match"):
        match = info["match"]
        print(f"\n✅ МАТЧ:")
        print(f"   Match ID: {match['id']}")
        print(f"   Статус: {match['status']}")
        if match.get("kickoff_time"):
            print(f"   Время: {match['kickoff_time']}")
    else:
        print("\n⚠️  МАТЧ НЕ СОЗДАН")
        print("   Аналитика недоступна без матча.")
        print()
        print("💡 Решение:")
        print("   1. Создать матч для этого видео:")
        print(f"      python create_match_for_video.py {video_id} 'Team 1' 'Team 2'")
        print()
        print("   2. Или через API:")
        print(f"      POST {BASE_URL}/api/analytics/videos/{video_id}/create-match/")
        print("      Body: {\"team1_name\": \"Team 1\", \"team2_name\": \"Team 2\"}")
        print()
        print("   3. Или перезагрузить видео с 'Create match automatically'")
        
        # Предложить создать матч интерактивно
        try:
            create = input("\n   Создать матч сейчас? (y/n): ").strip().lower()
            if create == 'y':
                team1 = input("   Название команды 1: ").strip()
                team2 = input("   Название команды 2: ").strip()
                
                if team1 and team2:
                    print(f"\n   Создаю матч: {team1} vs {team2}...")
                    match_response = requests.post(
                        f"{BASE_URL}/api/analytics/videos/{video_id}/create-match/",
                        json={
                            "team1_name": team1,
                            "team2_name": team2,
                            "period": 2,
                            "video_start_offset_ms": 3600000
                        }
                    )
                    match_response.raise_for_status()
                    match_data = match_response.json()
                    
                    print(f"   ✅ Матч создан! Match ID: {match_data['match_id']}")
                    print(f"   📊 Аналитика: {BASE_URL}{match_data['analytics_url']}")
                    
                    # Обновить информацию
                    info_response = requests.get(f"{BASE_URL}/api/analytics/videos/{video_id}/info/")
                    info = info_response.json()
                else:
                    print("   ❌ Названия команд не могут быть пустыми")
        except KeyboardInterrupt:
            print("\n   Отменено")
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
        
        if not info.get("match"):
            sys.exit(0)
    
    # Показать команды
    teams = info.get("teams", [])
    if teams:
        print(f"\n✅ КОМАНДЫ ({len(teams)}):")
        for team in teams:
            print(f"   Team ID: {team['team_id']}")
            print(f"   Название: {team['team_name']}")
            print(f"   Сторона: {team['side']}")
            print()
    else:
        print("\n⚠️  Команды не найдены")
    
    # Показать игроков
    players = info.get("players", [])
    if players:
        print(f"\n✅ ИГРОКИ ({len(players)}):")
        for player in players[:10]:  # Показать первых 10
            print(f"   Player ID: {player['player_id']}")
            print(f"   Имя: {player['player_name']}")
            print(f"   Позиция: {player['position']}")
            print(f"   Команда: {player['team_name']}")
            print()
        if len(players) > 10:
            print(f"   ... и еще {len(players) - 10} игроков")
    else:
        print("\n⚠️  ИГРОКИ НЕ СОЗДАНЫ")
        print("   Для метрик игроков нужно создать игроков через админку Django")
        print("   http://127.0.0.1:8000/admin/players/player/")
    
    # Показать статистику событий
    events = info.get("events", {})
    print(f"\n✅ СОБЫТИЯ:")
    print(f"   Всего: {events.get('total', 0)}")
    if events.get("by_type"):
        print("   По типам:")
        for event_type, count in events["by_type"].items():
            print(f"     - {event_type}: {count}")
    
    # Показать ссылки на аналитику
    analytics_urls = info.get("analytics_urls", {})
    if analytics_urls and "match_overview" in analytics_urls:
        print_section("Ссылки на аналитику")
        
        print("\n📊 Доступные API endpoints:")
        print(f"\n1. Обзор матча:")
        print(f"   GET {BASE_URL}{analytics_urls['match_overview']}")
        
        if "coach_summary" in analytics_urls:
            print(f"\n2. Тренерская аналитика:")
            print(f"   GET {BASE_URL}{analytics_urls['coach_summary']}")
        
        if "player_profile" in analytics_urls:
            print(f"\n3. Профиль игрока:")
            print(f"   GET {BASE_URL}{analytics_urls['player_profile']}")
        
        # Проверить аналитику
        print_section("Проверка аналитики матча")
        
        match_id = info["match"]["id"]
        print(f"\n3. Проверяю аналитику матча (Match ID: {match_id})...")
        try:
            analytics_response = requests.get(
                f"{BASE_URL}/api/analytics/matches/{match_id}/overview/"
            )
            analytics_response.raise_for_status()
            analytics = analytics_response.json()
            
            print("\n✅ АНАЛИТИКА МАТЧА:")
            
            # Показать метрики команд
            teams_data = analytics.get("teams", {})
            for side, team_data in teams_data.items():
                metrics = team_data.get("metrics", {})
                print(f"\n   {side.upper()} ({team_data.get('name', 'Unknown')}):")
                print(f"     Владение мячом: {metrics.get('possession_pct', 0)}%")
                print(f"     Потери: {metrics.get('turnovers', 0)}")
                print(f"     Темп: {metrics.get('tempo', 0)} событий/мин")
                if metrics.get('epi_avg'):
                    print(f"     EPI средний: {metrics['epi_avg']}")
            
            print("\n✅ Аналитика работает корректно!")
            
        except Exception as e:
            print(f"❌ Ошибка при проверке аналитики: {e}")
            print("   Возможно, события не были сохранены в БД")
    
    print_section("Готово!")
    print("\n💡 Полезные команды:")
    print(f"   - Получить информацию: curl {BASE_URL}/api/analytics/videos/{video_id}/info/")
    if match_id:
        print(f"   - Обзор матча: curl {BASE_URL}/api/analytics/matches/{match_id}/overview/")
    print(f"   - Список видео: curl {BASE_URL}/api/analytics/videos/")


if __name__ == "__main__":
    main()
