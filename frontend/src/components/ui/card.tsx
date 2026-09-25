import React from "react";
import { cn } from "@/lib/utils";

export function Card({
  className,
  topAccentColor,
  children,
  ...props
}: React.HTMLAttributes<HTMLDivElement> & { topAccentColor?: string }) {
  return (
    <div
      className={cn(
        "bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-xs overflow-hidden",
        topAccentColor && `border-t-4 ${topAccentColor}`,
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

export function CardHeader({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("p-5 border-b border-slate-100 dark:border-slate-800/80", className)} {...props}>
      {children}
    </div>
  );
}

export function CardTitle({ className, children, ...props }: React.HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3
      className={cn(
        "font-serif text-lg font-bold text-slate-900 dark:text-slate-100 tracking-tight",
        className
      )}
      {...props}
    >
      {children}
    </h3>
  );
}

export function CardContent({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("p-5", className)} {...props}>
      {children}
    </div>
  );
}
