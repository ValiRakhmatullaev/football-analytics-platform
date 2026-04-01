"use client";

import Link from "next/link";

interface QuickAction {
  href: string;
  label: string;
  icon: string;
  color: string;
}

interface QuickActionsProps {
  actions: QuickAction[];
}

export function QuickActions({ actions }: QuickActionsProps) {
  return (
    <div className="flex flex-wrap gap-3">
      {actions.map((action, index) => (
        <Link
          key={index}
          href={action.href}
          className={`
            inline-flex items-center gap-2 px-4 py-2
            rounded-lg font-medium text-white
            transition-all duration-200
            shadow-md hover:shadow-lg
            transform hover:scale-105
            ${action.color}
          `}
        >
          <span className="text-lg">{action.icon}</span>
          <span>{action.label}</span>
        </Link>
      ))}
    </div>
  );
}
