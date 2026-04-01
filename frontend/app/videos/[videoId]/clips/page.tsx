"use client";

import { useParams } from "next/navigation";
import VideoClipsViewer from "@/components/video/VideoClipsViewer";
import Link from "next/link";

export default function VideoClipsPage() {
  const params = useParams<{ videoId: string }>();
  const videoId = params.videoId;

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-6">
          <Link
            href="/upload"
            className="text-blue-600 hover:text-blue-800 text-sm"
          >
            ← Назад к загрузке
          </Link>
        </div>
        <VideoClipsViewer videoId={videoId} />
      </div>
    </div>
  );
}
