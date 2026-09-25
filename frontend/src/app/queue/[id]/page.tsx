"use client";

import React, { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, getMediaUrl } from "@/lib/api-client";
import { useAuth } from "@/context/AuthContext";
import { ZoomPanViewer } from "@/components/ui/zoom-pan-viewer";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { getRiskBadgeVariant, formatDate } from "@/lib/utils";
import {
  ArrowLeft,
  CheckCircle2,
  AlertTriangle,
  Stethoscope,
  Send,
  Calendar,
  User,
  ShieldAlert,
  HelpCircle,
  FileCheck,
} from "lucide-react";

export default function DoctorReviewWorkspace() {
  const params = useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const { user, isAuthenticated, isLoading: authLoading } = useAuth();
  const caseId = params.id as string;

  // Review Form State
  const [verdict, setVerdict] = useState<string>("Normal / Benign");
  const [explanation, setExplanation] = useState<string>("");
  const [recommendation, setRecommendation] = useState<string>("");
  const [formError, setFormError] = useState<string | null>(null);

  const {
    data: caseData,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["doctor-case", caseId],
    queryFn: () => api.getCase(caseId),
    enabled: !!caseId && isAuthenticated,
  });

  React.useEffect(() => {
    if (caseData) {
      if (caseData.doctor_verdict) setVerdict(caseData.doctor_verdict);
      if (caseData.doctor_explanation) setExplanation(caseData.doctor_explanation);
      if (caseData.recommendation) setRecommendation(caseData.recommendation);
    }
  }, [caseData]);

  const reviewMutation = useMutation({
    mutationFn: (payload: { doctor_verdict: string; doctor_explanation: string; recommendation: string }) =>
      api.submitReview(caseId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["doctor-queue"] });
      queryClient.invalidateQueries({ queryKey: ["doctor-case", caseId] });
      queryClient.invalidateQueries({ queryKey: ["clinical-stats"] });
      router.push("/queue");
    },
    onError: (err: any) => {
      setFormError(err.message || "Failed to submit clinical verdict.");
    },
  });

  if (authLoading || isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-24 space-y-4">
        <div className="h-10 w-10 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin" />
        <p className="text-sm text-slate-500 font-medium">Opening Case #{caseId} Review Workspace...</p>
      </div>
    );
  }

  if (user?.role !== "doctor") {
    return (
      <div className="max-w-md mx-auto py-16 text-center space-y-4">
        <ShieldAlert className="h-12 w-12 text-amber-600 mx-auto" />
        <h2 className="font-serif text-2xl font-bold">Physician Access Only</h2>
        <p className="text-sm text-slate-600 dark:text-slate-400">
          Only certified medical professionals have authorization to sign and record diagnostic reviews.
        </p>
        <Button onClick={() => router.push("/login")} className="bg-indigo-600 text-white">
          Sign In
        </Button>
      </div>
    );
  }

  if (error || !caseData) {
    return (
      <div className="max-w-md mx-auto py-16 text-center space-y-4">
        <AlertTriangle className="h-12 w-12 text-red-500 mx-auto" />
        <h2 className="font-serif text-xl font-bold">Case Not Found</h2>
        <Button onClick={() => router.push("/queue")} variant="outline" className="gap-2">
          <ArrowLeft className="h-4 w-4" /> Return to Queue
        </Button>
      </div>
    );
  }

  const handleSubmitReview = (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    // Validation
    if (!verdict) {
      setFormError("A diagnostic verdict selection is mandatory.");
      return;
    }
    if (!explanation.trim()) {
      setFormError("Clinical explanation and radiologic findings are mandatory.");
      return;
    }
    if (!recommendation.trim()) {
      setFormError("Patient next-step recommendations are mandatory.");
      return;
    }

    reviewMutation.mutate({
      doctor_verdict: verdict,
      doctor_explanation: explanation.trim(),
      recommendation: recommendation.trim(),
    });
  };

  const originalUrl = getMediaUrl(caseData.original_image_path);
  const gradcamUrl = caseData.gradcam_path ? getMediaUrl(caseData.gradcam_path) : undefined;
  const isAlreadyReviewed = !!caseData.doctor_verdict;

  return (
    <div className="space-y-6">
      {/* Top Navigation & Status Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-3 border-b border-slate-200 dark:border-slate-800">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="sm" onClick={() => router.push("/queue")} className="gap-1.5">
            <ArrowLeft className="h-4 w-4" /> Queue
          </Button>
          <div className="h-4 w-px bg-slate-300 dark:bg-slate-700" />
          <h1 className="font-serif text-2xl font-bold text-slate-900 dark:text-white">
            Case #{caseData.id} — Clinical Review
          </h1>
          <Badge variant={caseData.risk_band === "High Risk" ? "destructive" : "default"}>
            {caseData.risk_band}
          </Badge>
        </div>

        <div className="flex items-center gap-3 text-xs text-slate-500">
          <span className="flex items-center gap-1">
            <User className="h-3.5 w-3.5" /> Patient: <strong>{caseData.patient_name || `ID #${caseData.patient_id}`}</strong>
          </span>
          <span>•</span>
          <span className="flex items-center gap-1">
            <Calendar className="h-3.5 w-3.5" /> Submitted: {formatDate(caseData.created_at)}
          </span>
        </div>
      </div>

      {/* Main Workspace Layout (2 columns on desktop) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column: Radiograph Inspection & Grad-CAM (7 cols) */}
        <div className="lg:col-span-7 space-y-4">
          <div className="bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="font-serif text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <Stethoscope className="h-5 w-5 text-indigo-600" /> Radiograph Diagnostic Viewer
              </h2>
              <span className="text-xs text-slate-400">Mouse wheel to zoom • Drag to pan</span>
            </div>

            <ZoomPanViewer
              originalUrl={originalUrl}
              gradcamUrl={gradcamUrl}
              predictedClass={caseData.predicted_class}
              riskBand={caseData.risk_band}
            />
          </div>

          {/* Model Metrics Card */}
          <div className="grid grid-cols-3 gap-3">
            <div className="p-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-center">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">AI Classification</span>
              <p className="font-bold text-slate-900 dark:text-white mt-1 text-sm">
                {caseData.predicted_class || caseData.model_prediction || "AI Scanned"}
              </p>
            </div>
            <div className="p-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-center">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Calibrated Malignancy</span>
              <p className="font-bold text-indigo-600 dark:text-indigo-400 mt-1 text-sm">
                {(((caseData.calibrated_probability ?? caseData.cancer_probability ?? 0)) * 100).toFixed(1)}%
              </p>
            </div>
            <div className="p-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-center">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Triage Tier</span>
              <p className="font-bold mt-1 text-sm">
                <Badge variant={getRiskBadgeVariant(caseData.risk_band)} className="text-xs">
                  {caseData.risk_band}
                </Badge>
              </p>
            </div>
          </div>
        </div>

        {/* Right Column: Physician Review Form (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          <Card className="border-t-4 border-t-indigo-600 shadow-sm">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="font-serif text-lg font-bold flex items-center gap-2">
                  <FileCheck className="h-5 w-5 text-indigo-600" />
                  {isAlreadyReviewed ? "Edit Physician Verdict" : "Record Physician Verdict"}
                </CardTitle>
                {isAlreadyReviewed && (
                  <Badge variant="success" className="text-xs">
                    Already Reviewed
                  </Badge>
                )}
              </div>
              <p className="text-xs text-slate-500">
                All fields are required and will be appended to the official signed clinical export.
              </p>
            </CardHeader>
            <CardContent>
              {formError && (
                <div className="mb-4 p-3 rounded-lg bg-red-50 text-red-700 text-xs border border-red-200 dark:bg-red-950/40 dark:border-red-900 flex items-start gap-2">
                  <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
                  <span>{formError}</span>
                </div>
              )}

              <form onSubmit={handleSubmitReview} className="space-y-4">
                {/* Verdict Selection */}
                <div className="space-y-1.5">
                  <label htmlFor="verdict" className="text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
                    Diagnostic Verdict <span className="text-red-500">*</span>
                  </label>
                  <select
                    id="verdict"
                    value={verdict}
                    onChange={(e) => setVerdict(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  >
                    <option value="Normal / Benign">Normal / Benign (No Malignancy Detected)</option>
                    <option value="Cancer / Malignant">Cancer / Malignant (High Concern for Neoplasm)</option>
                    <option value="Inconclusive / Biopsy Recommended">Inconclusive (Biopsy / MRI Correlation Recommended)</option>
                    <option value="Non-Neoplastic Lesion">Non-Neoplastic Lesion (Infection / Trauma / Dysplasia)</option>
                  </select>
                </div>

                {/* Clinical Explanation Textarea */}
                <div className="space-y-1.5">
                  <label htmlFor="explanation" className="text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
                    Radiological Findings & Anatomical Explanation <span className="text-red-500">*</span>
                  </label>
                  <textarea
                    id="explanation"
                    rows={4}
                    value={explanation}
                    onChange={(e) => setExplanation(e.target.value)}
                    placeholder="Document anatomical location (e.g. distal femur, proximal tibia), cortical breach, periosteal reaction, matrix mineralization, and correlation with Grad-CAM heatmap..."
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 placeholder:text-slate-400 text-slate-900 dark:text-white"
                  />
                </div>

                {/* Recommendations Textarea */}
                <div className="space-y-1.5">
                  <label htmlFor="recommendation" className="text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
                    Clinical Recommendation & Action Plan <span className="text-red-500">*</span>
                  </label>
                  <textarea
                    id="recommendation"
                    rows={3}
                    value={recommendation}
                    onChange={(e) => setRecommendation(e.target.value)}
                    placeholder="Specify follow-up steps (e.g. Urgently refer to orthopedic oncology for core-needle biopsy, schedule contrast MRI, or routine 6-month surveillance)..."
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 placeholder:text-slate-400 text-slate-900 dark:text-white"
                  />
                </div>

                <div className="pt-2">
                  <Button
                    type="submit"
                    disabled={reviewMutation.isPending}
                    className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-2.5 gap-2 shadow-sm"
                  >
                    {reviewMutation.isPending ? (
                      <div className="h-4 w-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    ) : (
                      <>
                        <Send className="h-4 w-4" /> {isAlreadyReviewed ? "Update Diagnosis" : "Sign & Finalize Diagnosis"}
                      </>
                    )}
                  </Button>
                  <p className="text-[11px] text-slate-400 text-center mt-2">
                    Submitting logs an immutable audit event and marks case as REVIEWED.
                  </p>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
