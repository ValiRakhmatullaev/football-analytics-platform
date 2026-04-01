"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import VideoClipsViewer from "@/components/video/VideoClipsViewer";
import { BackButton } from "@/components/navigation/BackButton";

export default function VideoClipsPage() {
  const params = useParams<{ videoId: string }>();
  const videoId = params.videoId;

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-6 flex items-center justify-between gap-4">
          <BackButton href="/upload" label="← Назад к загрузке" />
          <Link
            href={`/videos/${videoId}/annotate`}
            className="px-4 py-2 rounded bg-blue-600 text-white text-sm hover:bg-blue-700"
          >
            Аннотация и нарезка
          </Link>
        </div>
        <VideoClipsViewer videoId={videoId} />
      </div>
    </div>
  );
}
