"use client";

import Link from "next/link";

interface ActionButton {
  href: string;
  label: string;
  description: string;
  icon: string;
  color: "blue" | "green" | "purple" | "orange" | "red";
  size?: "sm" | "md" | "lg";
}

interface ActionButtonsProps {
  buttons: ActionButton[];
  title?: string;
  columns?: 1 | 2 | 3 | 4;
}

export function ActionButtons({ 
  buttons, 
  title,
  columns = 3 
}: ActionButtonsProps) {
  const colorClasses = {
    blue: "bg-sky-500/10 hover:bg-sky-500/15 border-sky-400/40 text-sky-700 dark:text-sky-300",
    green: "bg-emerald-500/10 hover:bg-emerald-500/15 border-emerald-400/40 text-emerald-700 dark:text-emerald-300",
    purple: "bg-violet-500/10 hover:bg-violet-500/15 border-violet-400/40 text-violet-700 dark:text-violet-300",
    orange: "bg-amber-500/10 hover:bg-amber-500/15 border-amber-400/40 text-amber-700 dark:text-amber-300",
    red: "bg-rose-500/10 hover:bg-rose-500/15 border-rose-400/40 text-rose-700 dark:text-rose-300",
  };

  const sizeClasses = {
    sm: "p-3 text-sm",
    md: "p-4 text-base",
    lg: "p-6 text-lg",
  };

  const gridCols = {
    1: "grid-cols-1",
    2: "grid-cols-1 md:grid-cols-2",
    3: "grid-cols-1 md:grid-cols-2 lg:grid-cols-3",
    4: "grid-cols-1 md:grid-cols-2 lg:grid-cols-4",
  };

  return (
    <div className="space-y-4">
      {title && (
        <h2 className="text-xl font-semibold text-slate-900 dark:text-slate-50">{title}</h2>
      )}
      <div className={`grid ${gridCols[columns]} gap-4`}>
        {buttons.map((button, index) => (
          <Link
            key={index}
            href={button.href}
            className={`
              ${colorClasses[button.color]}
              ${sizeClasses[button.size || "md"]}
              rounded-2xl border font-medium
              transition-all duration-200 card-hover
              flex items-center justify-between gap-3
              text-left
              min-h-[92px]
            `}
          >
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-2xl bg-white/70 dark:bg-slate-900/40 flex items-center justify-center text-2xl shadow-sm">
                {button.icon}
              </div>
              <div>
                <div className="font-semibold text-sm sm:text-base">{button.label}</div>
                <div className="text-xs opacity-80 mt-1 max-w-xs">{button.description}</div>
              </div>
            </div>
            <span className="hidden sm:inline text-xs opacity-70">→</span>
          </Link>
        ))}
      </div>
    </div>
  );
}
