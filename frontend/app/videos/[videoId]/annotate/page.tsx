"use client";

import { useParams } from "next/navigation";
import { BackButton } from "@/components/navigation/BackButton";
import { VideoAnnotationPlayer } from "@/components/video/annotation";

/**
 * Interactive video annotation and clipping page.
 * - Review timeline with detected actions/events
 * - Trim clip boundaries (start/end) and add comments
 * - Frame-by-frame navigation, quick jump to actions, trim preview
 * - Save metadata to backend; export JSON for training
 */
export default function VideoAnnotatePage() {
  const params = useParams<{ videoId: string }>();
  const videoId = params.videoId;

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-6 flex items-center justify-between">
          <BackButton href={`/videos/${videoId}/clips`} label="← К клипам" />
          <h1 className="text-xl font-semibold text-gray-800">Аннотация и нарезка</h1>
        </div>
        <VideoAnnotationPlayer videoId={videoId} />
      </div>
    </div>
  );
}
