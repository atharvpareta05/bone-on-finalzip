"use client";

import React from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { api, getMediaUrl } from "@/lib/api-client";
import { useAuth } from "@/context/AuthContext";
import { ZoomPanViewer } from "@/components/ui/zoom-pan-viewer";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { getRiskBadgeVariant, getStatusBadgeVariant, formatDate } from "@/lib/utils";
import {
  ArrowLeft,
  Download,
  Calendar,
  User,
  CheckCircle2,
  Clock,
  AlertCircle,
  FileCheck,
  Stethoscope,
  Info,
} from "lucide-react";

export default function PatientCaseDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const caseId = params.id as string;

  const {
    data: caseData,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["case", caseId],
    queryFn: () => api.getCase(caseId),
    enabled: !!caseId && isAuthenticated,
  });

  if (authLoading || isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 space-y-4">
        <div className="h-10 w-10 border-4 border-teal-600 border-t-transparent rounded-full animate-spin" />
        <p className="text-sm text-slate-500 font-medium">Loading clinical case file #{caseId}...</p>
      </div>
    );
  }

  if (error || !caseData) {
    return (
      <div className="max-w-xl mx-auto py-12 text-center space-y-4">
        <div className="p-3 bg-red-50 text-red-600 rounded-full w-fit mx-auto dark:bg-red-950/50">
          <AlertCircle className="h-8 w-8" />
        </div>
        <h2 className="text-xl font-bold font-serif">Case Not Found or Access Denied</h2>
        <p className="text-sm text-slate-600 dark:text-slate-400">
          We could not load case #{caseId}. Please verify your network connection and case ownership permissions.
        </p>
        <Button onClick={() => router.push("/cases")} variant="outline" className="gap-2">
          <ArrowLeft className="h-4 w-4" /> Return to My Cases
        </Button>
      </div>
    );
  }

  const isReviewed = !!caseData.doctor_verdict;
  const originalUrl = getMediaUrl(caseData.original_image_path || caseData.image_url);
  const gradcamUrl = (caseData.gradcam_path || caseData.gradcam_url)
    ? getMediaUrl(caseData.gradcam_path || caseData.gradcam_url)
    : undefined;
  const prob = caseData.calibrated_probability ?? caseData.cancer_probability ?? 0;
  const pred = caseData.predicted_class || caseData.model_prediction || "AI Scanned";

  const handleDownloadPdf = async () => {
    try {
      const blob = await api.downloadPdfReport(caseData.id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `CareLens_Report_Case_${caseData.id}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      alert("Unable to download PDF report. Please verify case review completion.");
    }
  };

  return (
    <div className="space-y-6">
      {/* Header bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200 dark:border-slate-800">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="sm" onClick={() => router.push("/cases")} className="gap-1.5">
            <ArrowLeft className="h-4 w-4" /> Back to Cases
          </Button>
          <div className="h-4 w-px bg-slate-300 dark:bg-slate-700" />
          <h1 className="font-serif text-2xl font-bold text-slate-900 dark:text-white">
            Case #{caseData.id}
          </h1>
          <Badge variant={getStatusBadgeVariant(caseData.status)}>
            {caseData.status.toUpperCase()}
          </Badge>
        </div>

        <div className="flex items-center gap-3">
          {isReviewed ? (
            <Button
              onClick={handleDownloadPdf}
              className="bg-teal-600 hover:bg-teal-700 text-white gap-2 shadow-sm"
            >
              <Download className="h-4 w-4" /> Download Signed Report (PDF)
            </Button>
          ) : (
            <Badge variant="outline" className="text-amber-700 dark:text-amber-400 border-amber-300 gap-1.5 py-1.5 px-3">
              <Clock className="h-3.5 w-3.5" /> Awaiting Physician Review
            </Badge>
          )}
        </div>
      </div>

      {/* Case Details Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="border-t-2 border-t-slate-400">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs uppercase tracking-wider text-slate-500 font-semibold flex items-center gap-1.5">
              <Calendar className="h-3.5 w-3.5" /> Date Submitted
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="font-medium text-slate-900 dark:text-slate-100">
              {formatDate(caseData.created_at)}
            </p>
            <p className="text-xs text-slate-500 mt-0.5">{caseData.patient_name || "Patient"}</p>
          </CardContent>
        </Card>

        <Card className="border-t-2 border-t-teal-500">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs uppercase tracking-wider text-slate-500 font-semibold">
              AI Screen Prediction
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="font-bold text-lg text-slate-900 dark:text-slate-100">
              {pred}
            </p>
            <p className="text-xs text-slate-500 mt-0.5">Automated deep learning model</p>
          </CardContent>
        </Card>

        <Card className="border-t-2 border-t-blue-500">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs uppercase tracking-wider text-slate-500 font-semibold">
              Calibrated Probability
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="font-bold text-lg text-slate-900 dark:text-slate-100">
              {(prob * 100).toFixed(1)}%
            </p>
            <p className="text-xs text-slate-500 mt-0.5">Malignancy probability index</p>
          </CardContent>
        </Card>

        <Card className="border-t-2 border-t-emerald-500">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs uppercase tracking-wider text-slate-500 font-semibold">
              Risk Stratification
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Badge variant={getRiskBadgeVariant(caseData.risk_band)} className="text-sm px-2.5 py-0.5">
              {caseData.risk_band}
            </Badge>
            <p className="text-xs text-slate-500 mt-1">Clinical triage band</p>
          </CardContent>
        </Card>
      </div>

      {/* Main Radiograph Viewer & Grad-CAM */}
      <div className="space-y-3">
        <h2 className="font-serif text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
          Radiographic Imaging & Interpretability Analysis
        </h2>
        <ZoomPanViewer
          originalUrl={originalUrl}
          gradcamUrl={gradcamUrl}
          predictedClass={pred}
          riskBand={caseData.risk_band}
        />
      </div>

      {/* Physician Review Findings Section */}
      <Card className={`border-t-4 ${isReviewed ? "border-t-emerald-600" : "border-t-amber-500"}`}>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="font-serif text-xl flex items-center gap-2">
              <Stethoscope className="h-5 w-5 text-teal-600" /> Physician Clinical Findings & Final Recommendation
            </CardTitle>
            {isReviewed && (
              <Badge variant="success" className="gap-1">
                <CheckCircle2 className="h-3.5 w-3.5" /> Signed by Dr. {caseData.reviewed_by_doctor_id || "Physician"}
              </Badge>
            )}
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {isReviewed ? (
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pb-2 border-b border-slate-100 dark:border-slate-800">
                <div>
                  <span className="text-xs font-semibold uppercase text-slate-500">Clinical Verdict</span>
                  <p className="font-bold text-slate-900 dark:text-white mt-1 text-base">
                    {caseData.doctor_verdict}
                  </p>
                </div>
                <div>
                  <span className="text-xs font-semibold uppercase text-slate-500">Reviewed On</span>
                  <p className="font-medium text-slate-700 dark:text-slate-300 mt-1">
                    {formatDate(caseData.reviewed_at)}
                  </p>
                </div>
                <div>
                  <span className="text-xs font-semibold uppercase text-slate-500">Official Report</span>
                  <div className="mt-1">
                    <Button size="sm" onClick={handleDownloadPdf} variant="outline" className="gap-1.5 text-xs">
                      <FileCheck className="h-3.5 w-3.5 text-emerald-600" /> Export PDF
                    </Button>
                  </div>
                </div>
              </div>

              <div>
                <h4 className="text-xs font-semibold uppercase text-slate-500 tracking-wider">
                  Radiologist / Oncologist Clinical Explanation
                </h4>
                <div className="mt-1.5 p-4 rounded-lg bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-sm text-slate-800 dark:text-slate-200 whitespace-pre-wrap leading-relaxed">
                  {caseData.doctor_explanation || "No written notes provided."}
                </div>
              </div>

              <div>
                <h4 className="text-xs font-semibold uppercase text-slate-500 tracking-wider">
                  Actionable Recommendation & Next Steps
                </h4>
                <div className="mt-1.5 p-4 rounded-lg bg-teal-50/60 dark:bg-teal-950/30 border border-teal-200 dark:border-teal-900 text-sm text-teal-950 dark:text-teal-200 whitespace-pre-wrap leading-relaxed font-medium">
                  {caseData.recommendation || "Follow standard clinical monitoring protocol."}
                </div>
              </div>
            </div>
          ) : (
            <div className="p-6 rounded-xl bg-amber-50/60 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-900/50 flex items-start gap-4">
              <Clock className="h-6 w-6 text-amber-600 shrink-0 mt-0.5" />
              <div className="space-y-1">
                <h4 className="font-bold text-amber-900 dark:text-amber-300 text-sm">
                  Clinical Examination Pending
                </h4>
                <p className="text-xs text-amber-800 dark:text-amber-400 leading-relaxed">
                  Your submitted radiograph has been processed through AI screening and is queued for verification by a licensed orthopedic radiologist or oncologist. Once reviewed, official diagnostic findings, recommendations, and your signed clinical report will be posted here.
                </p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
