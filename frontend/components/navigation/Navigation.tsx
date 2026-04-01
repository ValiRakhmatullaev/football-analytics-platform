"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faFutbol, faHome, faUpload } from "@fortawesome/free-solid-svg-icons";
import type { IconDefinition } from "@fortawesome/fontawesome-svg-core";

export function Navigation() {
  const pathname = usePathname();

  const navItems: { href: string; label: string; icon: IconDefinition }[] = [
    {
      href: "/",
      label: "Главная",
      icon: faHome,
    },
    {
      href: "/upload",
      label: "Загрузить видео",
      icon: faUpload,
    },
  ];

  return (
    <nav className="sticky top-0 z-40 border-b border-slate-200/70 dark:border-slate-800/80 bg-white/80 dark:bg-slate-950/80 backdrop-blur-xl">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16 gap-4">
          <Link href="/" className="flex items-center gap-2">
            <div className="w-9 h-9 rounded-2xl bg-emerald-500/15 flex items-center justify-center text-lg">
              <FontAwesomeIcon icon={faFutbol} className="text-emerald-600" />
            </div>
            <div className="flex flex-col leading-tight">
              <span className="text-sm font-semibold tracking-tight text-slate-900 dark:text-white">
                Football Analytics
              </span>
              <span className="text-[11px] text-slate-500 dark:text-slate-400">
                Платформа анализа матчей
              </span>
            </div>
          </Link>

          <div className="flex items-center gap-1 sm:gap-2">
            {navItems.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`inline-flex items-center gap-1.5 rounded-full px-3 sm:px-4 py-1.5 text-sm font-medium transition-colors duration-150
                    ${
                      isActive
                        ? "bg-emerald-600 text-white shadow-sm shadow-emerald-500/40"
                        : "text-slate-600 dark:text-slate-300 hover:bg-slate-100/80 dark:hover:bg-slate-800/70"
                    }`}
                >
                  <FontAwesomeIcon icon={item.icon} className="text-base sm:text-sm" />
                  <span className="hidden sm:inline">{item.label}</span>
                </Link>
              );
            })}
          </div>
        </div>
      </div>
    </nav>
  );
}
