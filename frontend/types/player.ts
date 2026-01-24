export interface Team {
  id: number;
  name: string;
  logo_url?: string | null;
}

export interface Player {
  id: number;
  full_name: string;
  age: number;

  photo_url?: string | null;

  primary_position: string;
  secondary_positions?: string[];

  dominant_foot?: "left" | "right";

  current_team: Team;
  joined_team_at?: string | null;

  minutes_played_season: number;

  nationality?: string;
  shirt_number?: number;
}
