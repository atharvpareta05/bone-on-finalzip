"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { Bone, UploadCloud, FileText, CheckCircle2, Inbox, LogOut, Sun, Moon, AlertTriangle } from "lucide-react";
import { Button } from "./ui/button";

export function Navbar() {
  const { user, isAuthenticated, logout, sessionExpiryWarning, dismissWarning } = useAuth();
  const pathname = usePathname();
  const [isDark, setIsDark] = useState(false);

  useEffect(() => {
    const isDarkMode = document.documentElement.classList.contains("dark");
    setIsDark(isDarkMode);
  }, []);

  const toggleDarkMode = () => {
    if (document.documentElement.classList.contains("dark")) {
      document.documentElement.classList.remove("dark");
      localStorage.setItem("theme", "light");
      setIsDark(false);
    } else {
      document.documentElement.classList.add("dark");
      localStorage.setItem("theme", "dark");
      setIsDark(true);
    }
  };

  if (!isAuthenticated || !user) return null;

  return (
    <>
      {/* Session Expiry Inactivity Warning Bar */}
      {sessionExpiryWarning && (
        <div className="bg-amber-600 text-white text-xs px-4 py-2 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 shrink-0" />
            <span>
              Your session will expire in 5 minutes due to clinical inactivity. Would you like to remain signed in?
            </span>
          </div>
          <Button variant="secondary" size="sm" onClick={dismissWarning} className="h-7 text-xs">
            Extend Session
          </Button>
        </div>
      )}

      <header className="sticky top-0 z-40 bg-white/95 dark:bg-slate-900/95 backdrop-blur-md border-b border-slate-200 dark:border-slate-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          {/* Logo & Brand */}
          <div className="flex items-center gap-6">
            <Link href={user.role === "doctor" ? "/queue" : "/cases"} className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-lg bg-teal-700 dark:bg-teal-600 flex items-center justify-center text-white shadow-xs">
                <Bone className="w-5 h-5" />
              </div>
              <div>
                <span className="font-serif font-bold text-lg text-slate-900 dark:text-slate-100 tracking-tight flex items-center gap-1.5">
                  CareLens
                  <span className="text-[10px] font-sans font-semibold tracking-wider uppercase px-1.5 py-0.5 rounded bg-teal-100 text-teal-800 dark:bg-teal-950 dark:text-teal-300">
                    2.0
                  </span>
                </span>
                <span className="block text-[10px] text-slate-500 tracking-wider uppercase -mt-1">
                  Oncology Saliency Portal
                </span>
              </div>
            </Link>

            {/* Navigation Links */}
            <nav className="hidden md:flex items-center gap-1">
              {user.role === "patient" ? (
                <>
                  <Link
                    href="/cases"
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold transition-colors ${
                      pathname === "/cases"
                        ? "bg-teal-50 text-teal-800 dark:bg-teal-950/60 dark:text-teal-300"
                        : "text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-200"
                    }`}
                  >
                    <FileText className="w-4 h-4" />
                    My Submissions
                  </Link>
                  <Link
                    href="/upload"
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold transition-colors ${
                      pathname === "/upload"
                        ? "bg-teal-50 text-teal-800 dark:bg-teal-950/60 dark:text-teal-300"
                        : "text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-200"
                    }`}
                  >
                    <UploadCloud className="w-4 h-4" />
                    New Scan Upload
                  </Link>
                </>
              ) : (
                <>
                  <Link
                    href="/queue"
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold transition-colors ${
                      pathname === "/queue"
                        ? "bg-teal-50 text-teal-800 dark:bg-teal-950/60 dark:text-teal-300"
                        : "text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-200"
                    }`}
                  >
                    <Inbox className="w-4 h-4" />
                    Triage Queue
                  </Link>
                  <Link
                    href="/reviewed"
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold transition-colors ${
                      pathname === "/reviewed"
                        ? "bg-teal-50 text-teal-800 dark:bg-teal-950/60 dark:text-teal-300"
                        : "text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-200"
                    }`}
                  >
                    <CheckCircle2 className="w-4 h-4" />
                    Reviewed Archive
                  </Link>
                </>
              )}
            </nav>
          </div>

          {/* Right Action Cluster */}
          <div className="flex items-center gap-3">
            {/* Role Chip */}
            <div className="hidden sm:flex flex-col text-right">
              <span className="text-xs font-bold text-slate-800 dark:text-slate-200">{user.display_name}</span>
              <span className="text-[10px] uppercase font-semibold text-teal-700 dark:text-teal-400 tracking-wider">
                {user.role} workspace
              </span>
            </div>

            {/* Dark Mode Toggle */}
            <Button
              variant="ghost"
              size="sm"
              onClick={toggleDarkMode}
              title={isDark ? "Switch to Light Mode" : "Switch to Dark Mode"}
              aria-label="Toggle Dark Mode"
            >
              {isDark ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-slate-600" />}
            </Button>

            {/* Sign Out Button */}
            <Button variant="outline" size="sm" onClick={logout} title="Sign Out">
              <LogOut className="w-4 h-4" />
              <span className="hidden sm:inline">Sign Out</span>
            </Button>
          </div>
        </div>
      </header>
    </>
  );
}
