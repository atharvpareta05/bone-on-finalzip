"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import { Bone, Lock, User, AlertCircle, ArrowRight, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { DisclaimerBanner } from "@/components/ui/disclaimer-banner";

export default function LoginPage() {
  const { login } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password) {
      setError("Please enter both username and password.");
      return;
    }
    setError(null);
    setIsLoading(true);
    try {
      await login(username.trim(), password);
    } catch (err: any) {
      setError(err.message || "Invalid clinical credentials. Please check and try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleDemoFill = (u: string, p: string) => {
    setUsername(u);
    setPassword(p);
    setError(null);
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <div className="mx-auto w-12 h-12 rounded-xl bg-teal-700 dark:bg-teal-600 flex items-center justify-center text-white shadow-md mb-4">
          <Bone className="w-7 h-7" />
        </div>
        <h1 className="font-serif text-3xl font-extrabold text-slate-900 dark:text-slate-100 tracking-tight">
          CareLens Portal
        </h1>
        <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
          Bone Tumor Plain Radiograph Screening & Clinical Review
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <Card topAccentColor="border-t-teal-700">
          <CardHeader>
            <CardTitle>Sign In to Clinical Workspace</CardTitle>
          </CardHeader>
          <CardContent>
            {error && (
              <div
                role="alert"
                className="mb-4 p-3 rounded-lg bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900 text-xs text-red-700 dark:text-red-300 flex items-start gap-2"
              >
                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                <span>{error}</span>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Username
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                    <User className="w-4 h-4" />
                  </div>
                  <input
                    type="text"
                    required
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="e.g. doctor1 or patient1"
                    className="w-full pl-9 pr-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 focus:outline-hidden focus:ring-2 focus:ring-teal-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Password
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                    <Lock className="w-4 h-4" />
                  </div>
                  <input
                    type="password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full pl-9 pr-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 focus:outline-hidden focus:ring-2 focus:ring-teal-500"
                  />
                </div>
              </div>

              <Button type="submit" variant="primary" size="md" className="w-full mt-2" isLoading={isLoading}>
                Sign In
                <ArrowRight className="w-4 h-4 ml-1.5" />
              </Button>
            </form>

            {/* Demo Quick-Fill Hints */}
            <div className="mt-6 pt-4 border-t border-slate-100 dark:border-slate-800">
              <span className="block text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-2">
                Demo Accounts (Click to Fill)
              </span>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => handleDemoFill("doctor1", "doctor123")}
                  className="text-left p-2 rounded border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800 text-xs transition-colors"
                >
                  <span className="font-semibold block text-teal-800 dark:text-teal-300">Doctor View</span>
                  <span className="text-[11px] text-slate-500">doctor1 / doctor123</span>
                </button>
                <button
                  type="button"
                  onClick={() => handleDemoFill("patient1", "patient123")}
                  className="text-left p-2 rounded border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800 text-xs transition-colors"
                >
                  <span className="font-semibold block text-teal-800 dark:text-teal-300">Patient View</span>
                  <span className="text-[11px] text-slate-500">patient1 / patient123</span>
                </button>
              </div>
            </div>

            <div className="mt-5 text-center text-xs text-slate-600 dark:text-slate-400">
              New patient?{" "}
              <Link href="/register" className="font-semibold text-teal-700 dark:text-teal-400 hover:underline">
                Create self-registration account
              </Link>
            </div>
          </CardContent>
        </Card>

        <div className="mt-4">
          <DisclaimerBanner compact />
        </div>
      </div>
    </div>
  );
}
