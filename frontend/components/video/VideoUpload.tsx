"use client";

import { useState, useCallback } from "react";
import Link from "next/link";

interface UploadResponse {
  id: string;
  file_name: string;
  status: string;
  file_size: number;
  uploaded_at: string;
}

interface ProcessResponse {
  status: string;
  events_count: number;
  clips_created?: number;
  events_saved_to_db: boolean;
  match_id?: string;
  analytics_available: boolean;
  clips_url?: string;
  statistics: {
    events_by_type: Record<string, number>;
    avg_confidence: number;
  };
}

export default function VideoUpload() {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [uploadId, setUploadId] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [matchId, setMatchId] = useState<string>("");
  const [period, setPeriod] = useState<number>(2);
  const [offsetMs, setOffsetMs] = useState<number>(0);
  const [createMatch, setCreateMatch] = useState<boolean>(false);
  const [team1Name, setTeam1Name] = useState<string>("");
  const [team2Name, setTeam2Name] = useState<string>("");

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
    }
  };

  const handleUpload = useCallback(async () => {
    if (!file) {
      setError("Please select a file");
      return;
    }

    setUploading(true);
    setError(null);

    const formData = new FormData();
    formData.append("file", file);
    if (matchId) formData.append("match_id", matchId);
    if (period) formData.append("period", period.toString());
    if (offsetMs) formData.append("video_start_offset_ms", offsetMs.toString());
    if (createMatch) {
      formData.append("create_match", "true");
      formData.append("team1_name", team1Name);
      formData.append("team2_name", team2Name);
    }

    try {
      const response = await fetch("http://127.0.0.1:8000/api/analytics/videos/upload/", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `HTTP ${response.status}`);
      }

      const data: UploadResponse = await response.json();
      setUploadId(data.id);
      setStatus(data.status);
      setUploading(false);

      // Auto-start processing
      handleProcess(data.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
      setUploading(false);
    }
  }, [file, matchId, period, offsetMs]);

  const handleProcess = useCallback(async (videoId: string) => {
    setProcessing(true);
    setError(null);

    try {
      const response = await fetch(
        `http://127.0.0.1:8000/api/analytics/videos/${videoId}/process/`,
        {
          method: "POST",
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `HTTP ${response.status}`);
      }

      const data: ProcessResponse = await response.json();
      setStatus("completed");
      setProcessing(false);

      // Show success message with analytics link
      const messageParts: string[] = [];
      messageParts.push(`Processing complete! Detected ${data.events_count} events.`);
      
      // Safely stringify statistics
      try {
        const statsStr = JSON.stringify(data.statistics || {}, null, 2);
        if (statsStr && statsStr !== '{}') {
          messageParts.push(`Statistics: ${statsStr}`);
        }
      } catch (e) {
        console.warn("Failed to stringify statistics:", e);
      }
      
      if (data.analytics_available && data.match_id) {
        messageParts.push(`\n✅ Analytics available! View at: /matches/${data.match_id}`);
      } else if (data.events_count > 0 && !data.match_id) {
        messageParts.push(`\n⚠️ Events detected but no match linked. Analytics not available.`);
      }
      
      if (data.clips_created && data.clips_created > 0) {
        messageParts.push(`\n🎬 Created ${data.clips_created} video clips!`);
        setStatus(`completed - ${data.clips_created} clips created`);
      }
      
      // Use console.log instead of alert to avoid potential browser issues
      const message = messageParts.join('\n');
      console.log(message);
      
      // Show user-friendly notification
      if (data.clips_created && data.clips_created > 0) {
        setStatus(`✅ Completed! ${data.events_count} events, ${data.clips_created} clips created`);
      } else {
        setStatus(`✅ Completed! ${data.events_count} events detected`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Processing failed");
      setProcessing(false);
    }
  }, []);

  const checkStatus = useCallback(async (videoId: string) => {
    try {
      const response = await fetch(
        `http://127.0.0.1:8000/api/analytics/videos/${videoId}/status/`
      );

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      setStatus(data.status);

      if (data.status === "processing") {
        // Poll again after 2 seconds
        setTimeout(() => checkStatus(videoId), 2000);
      }
    } catch (err) {
      console.error("Status check failed:", err);
    }
  }, []);

  return (
    <div className="max-w-2xl mx-auto p-6 space-y-6">
      <h2 className="text-2xl font-semibold">Upload Video</h2>

      {/* File Input */}
      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-700">
          Video File
        </label>
        <input
          type="file"
          accept="video/*"
          onChange={handleFileChange}
          className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
          disabled={uploading || processing}
        />
        {file && (
          <p className="text-sm text-gray-600">
            Selected: {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
          </p>
        )}
      </div>

      {/* Optional Parameters */}
      <div className="space-y-4 border-t pt-4">
        <h3 className="text-lg font-medium">Optional Parameters</h3>

        <div className="flex items-center space-x-2">
          <input
            type="checkbox"
            id="create_match"
            checked={createMatch}
            onChange={(e) => setCreateMatch(e.target.checked)}
            className="rounded"
            disabled={uploading || processing}
          />
          <label htmlFor="create_match" className="text-sm font-medium text-gray-700">
            Create match automatically
          </label>
        </div>

        {createMatch ? (
          <div className="grid grid-cols-2 gap-4 p-4 bg-blue-50 rounded-md">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Team 1 Name *
              </label>
              <input
                type="text"
                value={team1Name}
                onChange={(e) => setTeam1Name(e.target.value)}
                placeholder="Home Team"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={uploading || processing}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Team 2 Name *
              </label>
              <input
                type="text"
                value={team2Name}
                onChange={(e) => setTeam2Name(e.target.value)}
                placeholder="Away Team"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={uploading || processing}
              />
            </div>
          </div>
        ) : (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Match ID (UUID)
            </label>
            <input
              type="text"
              value={matchId}
              onChange={(e) => setMatchId(e.target.value)}
              placeholder="Optional: Link to existing match"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={uploading || processing}
            />
            <p className="text-xs text-gray-500 mt-1">
              Leave empty and check "Create match" to auto-create
            </p>
          </div>
        )}

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Period
            </label>
            <select
              value={period}
              onChange={(e) => setPeriod(Number(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={uploading || processing}
            >
              <option value={1}>1st Half</option>
              <option value={2}>2nd Half</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Start Offset (ms)
            </label>
            <input
              type="number"
              value={offsetMs}
              onChange={(e) => setOffsetMs(Number(e.target.value))}
              placeholder="0"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={uploading || processing}
            />
            <p className="text-xs text-gray-500 mt-1">
              e.g., 3600000 for 60:00
            </p>
          </div>
        </div>
      </div>

      {/* Status */}
      {status && (
        <div className="p-4 bg-blue-50 rounded-md">
          <p className="text-sm font-medium text-blue-900">
            Status: <span className="font-normal">{status}</span>
          </p>
          {uploadId && (
            <>
              <p className="text-xs text-blue-700 mt-1">Video ID: {uploadId}</p>
              {(status.includes("completed") || status.includes("✅")) && (
                <div className="mt-3 space-y-2">
                  <Link
                    href={`/videos/${uploadId}/clips`}
                    className="inline-block px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 transition shadow-sm"
                  >
                    🎬 Просмотреть клипы
                  </Link>
                  <p className="text-xs text-blue-600">
                    Нажмите, чтобы просмотреть все созданные клипы
                  </p>
                </div>
              )}
            </>
          )}
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="p-4 bg-red-50 rounded-md">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      {/* Upload Button */}
      <button
        onClick={handleUpload}
        disabled={!file || uploading || processing}
        className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition"
      >
        {uploading
          ? "Uploading..."
          : processing
          ? "Processing..."
          : "Upload & Process Video"}
      </button>

      {/* Info */}
      <div className="text-sm text-gray-600 space-y-1">
        <p>• Supported formats: MP4, AVI, MOV, MKV, WebM</p>
        <p>• Maximum file size: 2GB</p>
        <p>• Processing may take several minutes depending on video length</p>
      </div>
    </div>
  );
}
