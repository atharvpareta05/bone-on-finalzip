"use client";

import React from "react";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  UploadCloud,
  FileText,
  Activity,
  ShieldCheck,
  Stethoscope,
  ChevronRight,
  Sparkles,
  Layers,
  ArrowRight,
} from "lucide-react";

export default function Home() {
  const { user, isAuthenticated } = useAuth();

  return (
    <div className="space-y-12 py-4">
      {/* Hero Section */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-teal-900 via-teal-800 to-slate-900 text-white p-8 sm:p-12 shadow-xl border border-teal-700/40">
        <div className="relative z-10 max-w-3xl space-y-5">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-teal-500/20 text-teal-200 border border-teal-400/30 text-xs font-semibold uppercase tracking-wider">
            <Sparkles className="h-3.5 w-3.5 text-teal-300" />
            Clinical Decision-Support Suite v2.0
          </div>
          <h1 className="font-serif text-3xl sm:text-5xl font-bold tracking-tight text-white leading-tight">
            Precision AI Assistance for Radiographic Bone Tumor Screening
          </h1>
          <p className="text-slate-200 text-base sm:text-lg leading-relaxed">
            CareLens combines deep transfer learning (ResNet-50) with class activation mapping (Grad-CAM) to provide transparent, interpretable visual evidence and calibrated risk stratification for clinical teams and patients.
          </p>
          <div className="pt-2 flex flex-wrap items-center gap-4">
            {isAuthenticated ? (
              user?.role === "doctor" ? (
                <Link href="/queue">
                  <Button size="lg" className="bg-teal-500 hover:bg-teal-400 text-slate-950 font-bold gap-2">
                    <Stethoscope className="h-5 w-5" /> Open Clinical Queue <ArrowRight className="h-4 w-4" />
                  </Button>
                </Link>
              ) : (
                <Link href="/upload">
                  <Button size="lg" className="bg-teal-500 hover:bg-teal-400 text-slate-950 font-bold gap-2">
                    <UploadCloud className="h-5 w-5" /> Upload New Radiograph <ArrowRight className="h-4 w-4" />
                  </Button>
                </Link>
              )
            ) : (
              <>
                <Link href="/login">
                  <Button size="lg" className="bg-teal-500 hover:bg-teal-400 text-slate-950 font-bold gap-2">
                    Sign In to Portal <ArrowRight className="h-4 w-4" />
                  </Button>
                </Link>
                <Link href="/register">
                  <Button size="lg" variant="outline" className="border-teal-300 text-teal-100 hover:bg-teal-800/40">
                    Patient Registration
                  </Button>
                </Link>
              </>
            )}
          </div>
        </div>

        {/* Ambient subtle backdrop effect */}
        <div className="absolute -top-24 -right-24 w-96 h-96 bg-teal-500/10 rounded-full blur-3xl pointer-events-none" />
      </div>

      {/* Feature & Architecture Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="border-t-4 border-t-teal-600 shadow-sm hover:shadow-md transition">
          <CardHeader>
            <div className="p-2.5 w-fit rounded-lg bg-teal-50 dark:bg-teal-950/60 text-teal-700 dark:text-teal-400 mb-2">
              <Layers className="h-6 w-6" />
            </div>
            <CardTitle className="font-serif text-xl">Interpretability-First ML</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-slate-600 dark:text-slate-400 space-y-2">
            <p>
              Integrated Grad-CAM gradient maps extract heatmaps straight from layer 4 convolution activations, revealing the exact anatomical regions driving inference.
            </p>
            <Badge variant="outline" className="text-teal-700 dark:text-teal-400 border-teal-300">
              Layer4 Hooks • PyTorch Native
            </Badge>
          </CardContent>
        </Card>

        <Card className="border-t-4 border-t-blue-600 shadow-sm hover:shadow-md transition">
          <CardHeader>
            <div className="p-2.5 w-fit rounded-lg bg-blue-50 dark:bg-blue-950/60 text-blue-700 dark:text-blue-400 mb-2">
              <Activity className="h-6 w-6" />
            </div>
            <CardTitle className="font-serif text-xl">Calibrated Risk Stratification</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-slate-600 dark:text-slate-400 space-y-2">
            <p>
              Rather than raw uncalibrated probabilities, cases are partitioned into clinical action tiers: Low Risk (&lt;0.35), Borderline (0.35–0.60), and High Risk (&ge;0.60).
            </p>
            <Badge variant="outline" className="text-blue-700 dark:text-blue-400 border-blue-300">
              Sensitivity &gt; 93.9% Target
            </Badge>
          </CardContent>
        </Card>

        <Card className="border-t-4 border-t-emerald-600 shadow-sm hover:shadow-md transition">
          <CardHeader>
            <div className="p-2.5 w-fit rounded-lg bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-400 mb-2">
              <ShieldCheck className="h-6 w-6" />
            </div>
            <CardTitle className="font-serif text-xl">Physician-in-the-Loop</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-slate-600 dark:text-slate-400 space-y-2">
            <p>
              AI outputs serve strictly as preliminary decision support. Orthopedic oncologists and radiologists submit binding diagnostic verdicts and clinical explanations.
            </p>
            <Badge variant="outline" className="text-emerald-700 dark:text-emerald-400 border-emerald-300">
              Audit Logged • JWT Protected
            </Badge>
          </CardContent>
        </Card>
      </div>

      {/* Quick Navigation Panels */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 pt-4">
        {/* Patient Portal Card */}
        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 flex flex-col justify-between shadow-sm">
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-teal-700 dark:text-teal-400 font-semibold text-sm">
              <FileText className="h-4 w-4" /> Patient Access
            </div>
            <h3 className="font-serif text-2xl font-bold text-slate-900 dark:text-white">
              Patient Portal & Submissions
            </h3>
            <p className="text-sm text-slate-600 dark:text-slate-400">
              Securely upload DICOM-converted or photographic bone radiographs for automated screening, monitor review progress, and access physician-approved reports.
            </p>
          </div>
          <div className="mt-6 flex items-center gap-3">
            <Link href="/upload" className="w-full sm:w-auto">
              <Button className="w-full sm:w-auto bg-teal-600 hover:bg-teal-700 text-white">
                Upload Scan <ChevronRight className="h-4 w-4 ml-1" />
              </Button>
            </Link>
            <Link href="/cases" className="w-full sm:w-auto">
              <Button variant="outline" className="w-full sm:w-auto">
                My Cases
              </Button>
            </Link>
          </div>
        </div>

        {/* Clinician Portal Card */}
        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 flex flex-col justify-between shadow-sm">
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-indigo-700 dark:text-indigo-400 font-semibold text-sm">
              <Stethoscope className="h-4 w-4" /> Clinician Workspace
            </div>
            <h3 className="font-serif text-2xl font-bold text-slate-900 dark:text-white">
              Doctor Triage & Review Queue
            </h3>
            <p className="text-sm text-slate-600 dark:text-slate-400">
              Inspect pending radiographs with interactive pan/zoom controls, evaluate Grad-CAM localization, record clinical findings, and generate signed PDF reports.
            </p>
          </div>
          <div className="mt-6 flex items-center gap-3">
            <Link href="/queue" className="w-full sm:w-auto">
              <Button className="w-full sm:w-auto bg-indigo-600 hover:bg-indigo-700 text-white">
                Review Queue <ChevronRight className="h-4 w-4 ml-1" />
              </Button>
            </Link>
            <Link href="/reviewed" className="w-full sm:w-auto">
              <Button variant="outline" className="w-full sm:w-auto">
                Reviewed Archive
              </Button>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
