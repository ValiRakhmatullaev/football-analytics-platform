"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

interface Match {
  id: string;
  kickoff_time: string;
  status: string;
}

export default function HomePage() {
  const [matches, setMatches] = useState<Match[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("http://127.0.0.1:8000/api/analytics/matches/")
      .then((res) => {
        if (!res.ok) {
          throw new Error(`HTTP ${res.status}`);
        }
        return res.json();
      })
      .then((data) => {
        setMatches(data);
      })
      .catch((err) => {
        console.error(err);
        setError("Failed to load matches");
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  if (loading) {
    return <div className="p-6">Loading matches…</div>;
  }

  if (error) {
    return <div className="p-6 text-red-600">{error}</div>;
  }

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-semibold">
          Football Analytics Platform
        </h1>
        <div className="flex gap-3">
          <Link
            href="/upload"
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition"
          >
            Upload Video
          </Link>
        </div>
      </div>

      {matches.length === 0 ? (
        <div className="text-gray-600">
          No matches available.
        </div>
      ) : (
        <ul className="space-y-3">
          {matches.map((match) => (
            <li
              key={match.id}
              className="rounded-lg border border-gray-200 p-4 hover:bg-gray-50 transition"
            >
              <Link href={`/matches/${match.id}`}>
                <div className="cursor-pointer">
                  <div className="font-medium">
                    Match ID: {match.id}
                  </div>
                  <div className="text-sm text-gray-600">
                    Kickoff:{" "}
                    {new Date(match.kickoff_time).toLocaleString()}
                  </div>
                  <div className="text-sm">
                    Status: {match.status}
                  </div>
                </div>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
