import React from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { FileQuestion, ArrowLeft } from "lucide-react";

export default function NotFound() {
  return (
    <div className="min-h-[50vh] flex items-center justify-center p-6">
      <div className="max-w-md w-full p-8 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-center space-y-4">
        <FileQuestion className="h-12 w-12 text-slate-400 mx-auto" />
        <h2 className="font-serif text-2xl font-bold">Page or Case Not Found</h2>
        <p className="text-sm text-slate-500">
          The requested clinical record, route, or resource could not be located.
        </p>
        <Link href="/">
          <Button variant="outline" className="gap-2">
            <ArrowLeft className="h-4 w-4" /> Return to CareLens Portal
          </Button>
        </Link>
      </div>
    </div>
  );
}
