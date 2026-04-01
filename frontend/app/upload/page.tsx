"use client";

import VideoUpload from "@/components/video/VideoUpload";
import { BackButton } from "@/components/navigation/BackButton";

export default function UploadPage() {
  return (
    <div className="min-h-screen bg-mesh py-8 sm:py-10">
      <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-6 animate-fade-in-up" style={{ animationDelay: "0ms" }}>
          <BackButton href="/" label="← Назад к главной" />
        </div>
        <VideoUpload />
      </div>
    </div>
  );
}
