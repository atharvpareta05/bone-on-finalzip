"use client";

import React, { useState, useRef } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { UploadCloud, FileImage, AlertCircle, CheckCircle2, ArrowRight, ShieldAlert, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { DisclaimerBanner } from "@/components/ui/disclaimer-banner";
import { RiskBadge } from "@/components/ui/badge";
import { casesApi } from "@/lib/api-client";
import { CaseResponse } from "@/types/api";

const MAX_SIZE_MB = 10;
const MIN_DIM = 64;
const MAX_DIM = 4096;

export default function UploadPage() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<CaseResponse | null>(null);

  const validateAndSelectFile = (file: File) => {
    setError(null);
    setAnalysisResult(null);

    // 1. File Type Check
    if (!["image/png", "image/jpeg", "image/jpg"].includes(file.type.toLowerCase())) {
      setError("Invalid file format. Only plain radiograph PNG or JPEG images are accepted.");
      return;
    }

    // 2. File Size Check
    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
      setError(`File size (${(file.size / (1024 * 1024)).toFixed(1)}MB) exceeds maximum permitted ${MAX_SIZE_MB}MB.`);
      return;
    }

    // 3. Dimension Check via HTML Image object
    const objectUrl = URL.createObjectURL(file);
    const img = new Image();
    img.onload = () => {
      if (img.width < MIN_DIM || img.height < MIN_DIM || img.width > MAX_DIM || img.height > MAX_DIM) {
        setError(
          `Image dimensions (${img.width}x${img.height}px) are outside allowed boundaries (${MIN_DIM}x${MIN_DIM} to ${MAX_DIM}x${MAX_DIM}px).`
        );
        URL.revokeObjectURL(objectUrl);
        return;
      }
      setSelectedFile(file);
      setPreviewUrl(objectUrl);
    };
    img.onerror = () => {
      setError("Could not parse image data. Please ensure the file is an intact image.");
      URL.revokeObjectURL(objectUrl);
    };
    img.src = objectUrl;
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSelectFile(e.target.files[0]);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSelectFile(e.dataTransfer.files[0]);
    }
  };

  const handleSubmit = async () => {
    if (!selectedFile) return;
    setError(null);
    setIsAnalyzing(true);

    try {
      const result = await casesApi.submitCase(selectedFile);
      setAnalysisResult(result);
    } catch (err: any) {
      setError(err.message || "Failed analyzing scan. Please ensure the backend server is reachable.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="mb-6">
        <h1 className="font-serif text-3xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">
          Submit Radiograph for Analysis
        </h1>
        <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
          Upload plain bone X-ray scans (PNG/JPEG) for automated feature saliency extraction and physician review.
        </p>
      </div>

      <DisclaimerBanner />

      {error && (
        <div
          role="alert"
          className="mb-6 p-4 rounded-xl bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900 text-sm text-red-700 dark:text-red-300 flex items-start gap-3"
        >
          <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
          <div>
            <strong className="block font-semibold">Upload Validation Error</strong>
            <span>{error}</span>
          </div>
        </div>
      )}

      {!analysisResult ? (
        <Card topAccentColor="border-t-teal-700">
          <CardHeader>
            <CardTitle>Radiograph Upload & Pre-Check</CardTitle>
          </CardHeader>
          <CardContent>
            {/* Drag & Drop Area */}
            <div
              onDragOver={(e) => e.preventDefault()}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className="border-2 border-dashed border-slate-300 dark:border-slate-700 hover:border-teal-600 dark:hover:border-teal-500 rounded-xl p-8 text-center cursor-pointer transition-colors bg-slate-50/50 dark:bg-slate-900/50"
            >
              <input
                ref={fileInputRef}
                type="file"
                accept="image/png,image/jpeg"
                onChange={handleFileChange}
                className="hidden"
              />

              {previewUrl ? (
                <div className="flex flex-col items-center">
                  <img
                    src={previewUrl}
                    alt="Radiograph Preview"
                    className="max-h-64 object-contain rounded-lg border border-slate-200 dark:border-slate-800 shadow-xs mb-3"
                  />
                  <span className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                    {selectedFile?.name} ({(selectedFile?.size! / (1024 * 1024)).toFixed(2)} MB)
                  </span>
                  <span className="text-[11px] text-teal-700 dark:text-teal-400 mt-1">
                    Click or drag another image to replace
                  </span>
                </div>
              ) : (
                <div className="flex flex-col items-center">
                  <div className="w-14 h-14 rounded-full bg-teal-50 dark:bg-teal-950/60 flex items-center justify-center text-teal-700 dark:text-teal-400 mb-3">
                    <UploadCloud className="w-8 h-8" />
                  </div>
                  <h3 className="font-semibold text-slate-800 dark:text-slate-200 text-sm">
                    Drag and drop your bone radiograph scan here
                  </h3>
                  <p className="text-xs text-slate-500 mt-1">Supports PNG or JPEG format up to 10MB</p>
                  <Button variant="outline" size="sm" className="mt-4 pointer-events-none">
                    Select File from Device
                  </Button>
                </div>
              )}
            </div>

            {selectedFile && (
              <div className="mt-6 flex items-center justify-end gap-3 border-t border-slate-100 dark:border-slate-800 pt-4">
                <Button
                  variant="outline"
                  size="md"
                  onClick={() => {
                    setSelectedFile(null);
                    setPreviewUrl(null);
                  }}
                  disabled={isAnalyzing}
                >
                  Cancel
                </Button>
                <Button variant="primary" size="md" onClick={handleSubmit} isLoading={isAnalyzing}>
                  {isAnalyzing ? "Executing Deep Model..." : "Run AI Analysis & Queue Case"}
                  <ArrowRight className="w-4 h-4 ml-1.5" />
                </Button>
              </div>
            )}

            {isAnalyzing && (
              <div className="mt-6 p-4 rounded-xl bg-teal-50/50 dark:bg-teal-950/20 border border-teal-200 dark:border-teal-900 flex items-center gap-3">
                <Loader2 className="w-5 h-5 text-teal-700 dark:text-teal-400 animate-spin shrink-0" />
                <div className="text-xs text-teal-900 dark:text-teal-200">
                  <span className="font-semibold block">Extracting Deep Convolutional Features</span>
                  Computing Grad-CAM layer4 saliency attention maps and evaluating risk probability...
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      ) : (
        /* Analysis Results Card */
        <Card topAccentColor="border-t-teal-700">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>AI Screening Analysis Complete</CardTitle>
                <span className="text-xs text-slate-500 font-mono">Case ID: {analysisResult.id}</span>
              </div>
              <RiskBadge riskBand={analysisResult.risk_band} />
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Scan Images Preview */}
              <div className="flex flex-col gap-2">
                <span className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                  Grad-CAM Visual Saliency
                </span>
                <div className="bg-black rounded-lg p-2 flex items-center justify-center border border-slate-800">
                  {analysisResult.gradcam_url ? (
                    <img
                      src={casesApi.getMediaUrl(analysisResult.id, "gradcam")}
                      alt="Grad-CAM Overlay"
                      className="max-h-64 object-contain rounded"
                    />
                  ) : (
                    <div className="text-xs text-slate-400 p-8">Saliency map generating...</div>
                  )}
                </div>
                <span className="text-[11px] text-slate-500">
                  Focal warm colors (red/yellow) indicate anatomical regions driving model prediction.
                </span>
              </div>

              {/* Assessment Metrics */}
              <div className="flex flex-col justify-between">
                <div className="space-y-4">
                  <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
                    <span className="text-xs text-slate-500 uppercase font-semibold tracking-wider block">
                      Screening Projection
                    </span>
                    <span className="text-lg font-bold text-slate-900 dark:text-slate-100 block mt-0.5">
                      {analysisResult.model_prediction}
                    </span>
                    <div className="mt-3 flex items-baseline gap-2">
                      <span className="text-2xl font-bold font-serif text-teal-800 dark:text-teal-300">
                        {(analysisResult.cancer_probability * 100).toFixed(1)}%
                      </span>
                      <span className="text-xs text-slate-500">Calibrated Malignancy Risk</span>
                    </div>
                  </div>

                  <div className="p-3.5 rounded-lg bg-teal-50 dark:bg-teal-950/40 border border-teal-200 dark:border-teal-900 text-xs text-teal-900 dark:text-teal-200 flex items-start gap-2">
                    <CheckCircle2 className="w-4 h-4 text-teal-700 dark:text-teal-400 shrink-0 mt-0.5" />
                    <span>
                      This case has been registered in the hospital PACS queue. An attending radiologist or oncologist
                      will review your scan and provide formal diagnostic notes.
                    </span>
                  </div>
                </div>

                <div className="mt-6 flex items-center gap-3">
                  <Button
                    variant="outline"
                    size="md"
                    className="flex-1"
                    onClick={() => {
                      setSelectedFile(null);
                      setPreviewUrl(null);
                      setAnalysisResult(null);
                    }}
                  >
                    Upload Another Scan
                  </Button>
                  <Link href={`/cases/${analysisResult.id}`} className="flex-1">
                    <Button variant="primary" size="md" className="w-full">
                      View Full Case
                      <ArrowRight className="w-4 h-4 ml-1.5" />
                    </Button>
                  </Link>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
