"use client";

import { Player } from "@/types/player";

/* =======================
   TYPES
   ======================= */

interface PlayerHeaderProps {
  player: Player;
  seasonStart: string;
}

/* =======================
   COMPONENT
   ======================= */

export function PlayerHeader({
  player,
  seasonStart,
}: PlayerHeaderProps) {
  return (
    <div className="flex items-start gap-6">
      {/* Photo */}
      <div className="h-20 w-20 rounded-xl bg-gray-100 flex items-center justify-center text-gray-400 text-sm">
        {player.photo_url ? (
          <img
            src={player.photo_url}
            alt={player.full_name}
            className="h-full w-full rounded-xl object-cover"
          />
        ) : (
          <span>No photo</span>
        )}
      </div>

      {/* Main info */}
      <div className="flex-1 space-y-1">
        {/* Name */}
        <h2 className="text-lg font-semibold">
          {player.full_name}
        </h2>

        {/* Position */}
        <div className="text-sm text-gray-600">
          {player.primary_position}
        </div>

        {/* Team */}
        {player.current_team ? (
          <div className="flex items-center gap-2 text-sm text-gray-700">
            {player.current_team.logo_url && (
              <img
                src={player.current_team.logo_url}
                alt={player.current_team.name}
                className="h-4 w-4 object-contain"
              />
            )}
            <span>{player.current_team.name}</span>
          </div>
        ) : (
          <div className="text-sm text-gray-400">
            Match context only
          </div>
        )}

        {/* Meta */}
        <div className="flex flex-wrap gap-3 text-xs text-gray-500 mt-1">
          {player.nationality && (
            <span>Nationality: {player.nationality}</span>
          )}

          {player.shirt_number && (
            <span>#{player.shirt_number}</span>
          )}

          <span>
            Minutes played: {player.minutes_played_season}
          </span>
        </div>
      </div>
    </div>
  );
}
