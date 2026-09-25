import test from "node:test";
import assert from "node:assert/strict";
import {
  UPLOAD_LIMITS,
  validateUploadFile,
  validateImageDimensions,
  validateReviewForm,
  computeRiskBand,
} from "../lib/validation.ts";

test("Upload File Size and MIME Type Validation", async (t) => {
  await t.test("accepts valid PNG within size limits", () => {
    const file = { size: 2 * 1024 * 1024, type: "image/png" };
    const res = validateUploadFile(file);
    assert.equal(res.valid, true);
    assert.equal(res.error, undefined);
  });

  await t.test("accepts valid JPEG within size limits", () => {
    const file = { size: 500 * 1024, type: "image/jpeg" };
    const res = validateUploadFile(file);
    assert.equal(res.valid, true);
  });

  await t.test("rejects files exceeding 10MB limit", () => {
    const file = { size: 11 * 1024 * 1024, type: "image/png" };
    const res = validateUploadFile(file);
    assert.equal(res.valid, false);
    assert.match(res.error || "", /exceeds the 10MB limit/);
  });

  await t.test("rejects empty files (0 bytes)", () => {
    const file = { size: 0, type: "image/png" };
    const res = validateUploadFile(file);
    assert.equal(res.valid, false);
    assert.match(res.error || "", /empty/);
  });

  await t.test("rejects disallowed file extensions (e.g. PDF, executable, text)", () => {
    const file = { size: 1024, type: "application/pdf" };
    const res = validateUploadFile(file);
    assert.equal(res.valid, false);
    assert.match(res.error || "", /Unsupported file format/);
  });
});

test("Image Dimensions Validation", async (t) => {
  await t.test("accepts standard 224x224 and 1024x1024 radiographs", () => {
    assert.equal(validateImageDimensions(224, 224).valid, true);
    assert.equal(validateImageDimensions(1024, 1024).valid, true);
  });

  await t.test("rejects sub-minimum resolution (<64px)", () => {
    const res = validateImageDimensions(32, 224);
    assert.equal(res.valid, false);
    assert.match(res.error || "", /must be between 64px and 4096px/);
  });

  await t.test("rejects excessive resolution (>4096px)", () => {
    const res = validateImageDimensions(5000, 224);
    assert.equal(res.valid, false);
    assert.match(res.error || "", /must be between 64px and 4096px/);
  });
});

test("Review Form Required Fields Validation", async (t) => {
  await t.test("accepts fully completed clinical review", () => {
    const payload = {
      doctor_verdict: "Cancer / Malignant",
      doctor_explanation: "Cortical destruction noted in distal femur.",
      recommendation: "Immediate referral for surgical biopsy.",
    };
    const res = validateReviewForm(payload);
    assert.equal(res.valid, true);
  });

  await t.test("rejects missing diagnostic verdict", () => {
    const payload = {
      doctor_verdict: "",
      doctor_explanation: "Cortical destruction noted in distal femur.",
      recommendation: "Immediate referral for surgical biopsy.",
    };
    const res = validateReviewForm(payload);
    assert.equal(res.valid, false);
    assert.match(res.error || "", /verdict/i);
  });

  await t.test("rejects missing or too-short clinical explanation", () => {
    const payload = {
      doctor_verdict: "Normal / Benign",
      doctor_explanation: "ok",
      recommendation: "Routine 1-year follow-up.",
    };
    const res = validateReviewForm(payload);
    assert.equal(res.valid, false);
    assert.match(res.error || "", /explanation/i);
  });

  await t.test("rejects missing recommendation", () => {
    const payload = {
      doctor_verdict: "Normal / Benign",
      doctor_explanation: "Intact bony trabeculae without focal lytic lesion.",
      recommendation: "",
    };
    const res = validateReviewForm(payload);
    assert.equal(res.valid, false);
    assert.match(res.error || "", /recommendation/i);
  });
});

test("Risk Band Boundary Cutoffs Matching Backend", async (t) => {
  await t.test("probabilities < 0.35 classify as Low Risk", () => {
    assert.equal(computeRiskBand(0.0), "Low Risk");
    assert.equal(computeRiskBand(0.15), "Low Risk");
    assert.equal(computeRiskBand(0.34999), "Low Risk");
  });

  await t.test("probabilities between 0.35 and 0.5999 classify as Borderline", () => {
    assert.equal(computeRiskBand(0.35), "Borderline");
    assert.equal(computeRiskBand(0.48), "Borderline");
    assert.equal(computeRiskBand(0.59999), "Borderline");
  });

  await t.test("probabilities >= 0.60 classify as High Risk", () => {
    assert.equal(computeRiskBand(0.60), "High Risk");
    assert.equal(computeRiskBand(0.75), "High Risk");
    assert.equal(computeRiskBand(1.0), "High Risk");
  });
});
