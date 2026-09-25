import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/Providers";
import { Navbar } from "@/components/Navbar";
import { DisclaimerBanner } from "@/components/ui/disclaimer-banner";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
});

export const metadata: Metadata = {
  title: "CareLens — AI-Assisted Bone Tumor Decision Support",
  description: "Clinical grade bone lesion classification, calibrated risk stratifications, and Grad-CAM interpretability workspace.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${inter.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-100 font-sans">
        <Providers>
          <DisclaimerBanner />
          <Navbar />
          <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
            {children}
          </main>
          <footer className="border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 py-6 text-center text-xs text-slate-500">
            <p>
              CareLens Clinical Decision-Support System v2.0 • For research and investigational decision-support only • Not a standalone diagnostic device.
            </p>
          </footer>
        </Providers>
      </body>
    </html>
  );
}
