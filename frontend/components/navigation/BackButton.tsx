"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";

interface BackButtonProps {
  href?: string;
  label?: string;
  className?: string;
}

export function BackButton({ 
  href, 
  label = "← Назад",
  className = ""
}: BackButtonProps) {
  const router = useRouter();

  const handleClick = () => {
    if (href) {
      router.push(href);
    } else {
      router.back();
    }
  };

  return (
    <button
      onClick={handleClick}
      className={`
        inline-flex items-center gap-2 px-4 py-2
        text-sm font-medium text-gray-700
        bg-white border border-gray-300 rounded-lg
        hover:bg-gray-50 hover:text-gray-900
        transition-all duration-200
        shadow-sm hover:shadow-md
        ${className}
      `}
    >
      <span>{label}</span>
    </button>
  );
}
