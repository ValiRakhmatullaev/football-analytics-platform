"""
Data exporter module for converting detected events to Django-compatible format.
Handles mapping of detected events to Django Event model structure.
"""

import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import logging

from video_analytics.event_detector import DetectedEvent, EventType

logger = logging.getLogger(__name__)


class DjangoEventExporter:
    """
    Exports detected events to Django-compatible format.
    Can export to JSON for manual import or directly to Django via API/ORM.
    """

    def __init__(self, match_id: Optional[str] = None, period: int = 2):
        """
        Initialize exporter.

        Args:
            match_id: Django Match UUID (optional, for direct export)
            period: Match period (1=1st half, 2=2nd half, etc.)
        """
        self.match_id = match_id
        self.period = period

    def events_to_django_format(self, events: List[DetectedEvent], 
                               video_start_offset_ms: int = 0) -> List[Dict[str, Any]]:
        """
        Convert detected events to Django Event model format.

        Args:
            events: List of DetectedEvent objects
            video_start_offset_ms: Offset in milliseconds (e.g., if video starts at 60:00)

        Returns:
            List of dictionaries compatible with Django Event model
        """
        django_events = []

        for event in events:
            # Calculate timestamp from match start (not video start)
            timestamp_ms = video_start_offset_ms + event.timestamp_ms

            django_event = {
                "event_type": event.event_type.value,  # "pass", "shot", etc.
                "timestamp_ms": timestamp_ms,
                "period": self.period,
                "x": round(event.x, 2) if event.x is not None else None,
                "y": round(event.y, 2) if event.y is not None else None,
                "confidence": round(event.confidence, 3),
                "outcome": event.outcome,
                # These will need to be mapped to actual Django objects
                "team_id": event.team_id,  # Will be mapped to Team UUID
                "player_id": event.player_id,  # Will be mapped to Player UUID
                "secondary_player_id": None,  # For pass receivers, etc.
                "related_event_id": None,  # For event chains
                "metadata": event.metadata,
            }

            django_events.append(django_event)

        return django_events

    def export_to_json(self, events: List[DetectedEvent], output_path: str,
                       video_start_offset_ms: int = 0, metadata: Optional[Dict] = None):
        """
        Export events to JSON file for manual review/import.

        Args:
            events: List of DetectedEvent objects
            output_path: Path to output JSON file
            video_start_offset_ms: Offset in milliseconds
            metadata: Additional metadata to include
        """
        django_events = self.events_to_django_format(events, video_start_offset_ms)

        export_data = {
            "exported_at": datetime.now().isoformat(),
            "match_id": self.match_id,
            "period": self.period,
            "video_start_offset_ms": video_start_offset_ms,
            "total_events": len(django_events),
            "events": django_events,
            "metadata": metadata or {},
        }

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Exported {len(django_events)} events to {output_path}")

    def export_to_django(self, events: List[DetectedEvent], 
                        video_start_offset_ms: int = 0,
                        team_mapping: Optional[Dict[str, str]] = None,
                        player_mapping: Optional[Dict[str, str]] = None):
        """
        Export events directly to Django database.

        Args:
            events: List of DetectedEvent objects
            video_start_offset_ms: Offset in milliseconds
            team_mapping: Mapping from detected team_id to Django Team UUID
            player_mapping: Mapping from detected player_id to Django Player UUID

        Returns:
            List of created Django Event objects
        """
        # This requires Django to be available
        try:
            import django
            from django.apps import apps

            # Ensure Django is configured
            if not django.apps.apps.ready:
                raise RuntimeError("Django apps not ready. Call django.setup() first.")

            Event = apps.get_model("events", "Event")
            Team = apps.get_model("teams", "Team")
            Player = apps.get_model("players", "Player")
            Match = apps.get_model("competitions", "Match")

            if not self.match_id:
                raise ValueError("match_id required for Django export")

            match = Match.objects.get(id=self.match_id)
            django_events = []

            for event in events:
                timestamp_ms = video_start_offset_ms + event.timestamp_ms

                # Map team
                team = None
                if event.team_id and team_mapping:
                    team_id = team_mapping.get(event.team_id)
                    if team_id:
                        team = Team.objects.get(id=team_id)
                elif event.team_id:
                    # Try direct lookup
                    try:
                        team = Team.objects.get(id=event.team_id)
                    except Team.DoesNotExist:
                        logger.warning(f"Team not found: {event.team_id}")

                # Map player
                player = None
                if event.player_id and player_mapping:
                    player_id = player_mapping.get(event.player_id)
                    if player_id:
                        player = Player.objects.get(id=player_id)
                elif event.player_id:
                    try:
                        player = Player.objects.get(id=event.player_id)
                    except Player.DoesNotExist:
                        logger.warning(f"Player not found: {event.player_id}")

                # Create event
                django_event = Event.objects.create(
                    match=match,
                    team=team,
                    player=player,
                    event_type=event.event_type.value,
                    timestamp_ms=timestamp_ms,
                    period=self.period,
                    x=event.x,
                    y=event.y,
                    confidence=event.confidence,
                    outcome=event.outcome,
                )

                django_events.append(django_event)

            logger.info(f"Created {len(django_events)} events in Django database")
            return django_events

        except ImportError:
            logger.error("Django not available. Use export_to_json instead.")
            raise
        except Exception as e:
            logger.error(f"Error exporting to Django: {e}")
            raise
