"use client";

import React, { useState, useRef } from "react";
import { ZoomIn, ZoomOut, RotateCcw, Eye, Layers, Columns } from "lucide-react";
import { Button } from "./button";

interface ZoomPanViewerProps {
  originalUrl: string;
  gradcamUrl?: string | null;
  altText?: string;
  predictedClass?: string;
  riskBand?: string;
}

export function ZoomPanViewer({
  originalUrl,
  gradcamUrl,
  altText = "Bone Radiograph",
  predictedClass,
  riskBand,
}: ZoomPanViewerProps) {
  const [scale, setScale] = useState(1);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [viewMode, setViewMode] = useState<"side-by-side" | "overlay" | "original">("side-by-side");

  const containerRef = useRef<HTMLDivElement>(null);

  const handleZoomIn = () => setScale((prev) => Math.min(prev + 0.35, 4.0));
  const handleZoomOut = () => setScale((prev) => Math.max(prev - 0.35, 1.0));
  const handleReset = () => {
    setScale(1);
    setPosition({ x: 0, y: 0 });
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    if (scale <= 1) return;
    setIsDragging(true);
    setDragStart({ x: e.clientX - position.x, y: e.clientY - position.y });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging) return;
    setPosition({
      x: e.clientX - dragStart.x,
      y: e.clientY - dragStart.y,
    });
  };

  const handleMouseUp = () => setIsDragging(false);

  return (
    <div className="flex flex-col gap-2 w-full select-none">
      {/* Viewer Toolbar */}
      <div className="flex items-center justify-between bg-slate-100 dark:bg-slate-800/80 px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 text-xs">
        <div className="flex items-center gap-1">
          {gradcamUrl && (
            <>
              <Button
                variant={viewMode === "side-by-side" ? "primary" : "ghost"}
                size="sm"
                onClick={() => setViewMode("side-by-side")}
                title="Side by Side"
              >
                <Columns className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">Side-by-Side</span>
              </Button>
              <Button
                variant={viewMode === "overlay" ? "primary" : "ghost"}
                size="sm"
                onClick={() => setViewMode("overlay")}
                title="Grad-CAM Overlay"
              >
                <Layers className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">Grad-CAM</span>
              </Button>
              <Button
                variant={viewMode === "original" ? "primary" : "ghost"}
                size="sm"
                onClick={() => setViewMode("original")}
                title="Original Plain Scan"
              >
                <Eye className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">Original</span>
              </Button>
            </>
          )}
        </div>

        {/* Zoom Controls */}
        <div className="flex items-center gap-1">
          <span className="text-slate-500 font-mono text-[11px] mr-1">{Math.round(scale * 100)}%</span>
          <Button variant="ghost" size="sm" onClick={handleZoomOut} disabled={scale <= 1} title="Zoom Out">
            <ZoomOut className="w-3.5 h-3.5" />
          </Button>
          <Button variant="ghost" size="sm" onClick={handleZoomIn} disabled={scale >= 4} title="Zoom In">
            <ZoomIn className="w-3.5 h-3.5" />
          </Button>
          <Button variant="ghost" size="sm" onClick={handleReset} title="Reset Pan/Zoom">
            <RotateCcw className="w-3.5 h-3.5" />
          </Button>
        </div>
      </div>

      {/* Radiograph Viewport */}
      <div
        ref={containerRef}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        className="relative bg-black rounded-lg border border-slate-800 overflow-hidden min-h-[360px] flex items-center justify-center cursor-grab active:cursor-grabbing"
      >
        <div
          style={{
            transform: `translate(${position.x}px, ${position.y}px) scale(${scale})`,
            transition: isDragging ? "none" : "transform 0.15s ease-out",
          }}
          className="flex items-center justify-center gap-4 max-w-full"
        >
          {viewMode === "side-by-side" && gradcamUrl ? (
            <div className="grid grid-cols-2 gap-3 p-3">
              <div className="flex flex-col items-center">
                <img
                  src={originalUrl}
                  alt={`${altText} - Original`}
                  className="max-h-[380px] object-contain rounded border border-neutral-700 pointer-events-none"
                />
                <span className="text-[11px] text-slate-400 mt-1">Native Scan</span>
              </div>
              <div className="flex flex-col items-center">
                <img
                  src={gradcamUrl}
                  alt={`${altText} - Grad-CAM Overlay`}
                  className="max-h-[380px] object-contain rounded border border-neutral-700 pointer-events-none"
                />
                <span className="text-[11px] text-slate-400 mt-1">Grad-CAM Overlay</span>
              </div>
            </div>
          ) : viewMode === "overlay" && gradcamUrl ? (
            <div className="p-3 flex flex-col items-center">
              <img
                src={gradcamUrl}
                alt={`${altText} - Grad-CAM Overlay`}
                className="max-h-[420px] object-contain rounded border border-neutral-700 pointer-events-none"
              />
            </div>
          ) : (
            <div className="p-3 flex flex-col items-center">
              <img
                src={originalUrl}
                alt={`${altText} - Original Scan`}
                className="max-h-[420px] object-contain rounded border border-neutral-700 pointer-events-none"
              />
            </div>
          )}
        </div>
      </div>

      {/* Grad-CAM Heatmap Interpretation Legend */}
      {gradcamUrl && (
        <div className="flex items-center justify-between text-xs text-slate-600 dark:text-slate-400 bg-slate-50 dark:bg-slate-900 px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-800">
          <span className="font-semibold text-slate-700 dark:text-slate-300">Grad-CAM Saliency:</span>
          <div className="flex items-center gap-2">
            <span className="text-[11px]">Low Attention (Blue)</span>
            <div className="w-24 h-2 rounded bg-gradient-to-r from-blue-600 via-yellow-400 to-red-600 border border-slate-300 dark:border-slate-700" />
            <span className="text-[11px]">Focal Lesion (Red)</span>
          </div>
        </div>
      )}
    </div>
  );
}
