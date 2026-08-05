"use client";

import { useState } from "react";

import { ArchitectureReviewForm } from "@/components/review/architecture-review-form";
import { ArchitectureReviewReport } from "@/components/review/architecture-review-report";
import { ApiError } from "@/lib/errors";
import { DEFAULT_REVIEW_FORM_VALUES } from "@/lib/review-form";
import { validateReviewForm } from "@/lib/validate-review-form";
import { submitArchitectureReview } from "@/services/review";
import type {
  ArchitectureReviewFormValues,
  ArchitectureReviewResponse,
} from "@/types/review";

export function ArchitectureReviewWorkspace() {
  const [values, setValues] = useState<ArchitectureReviewFormValues>(
    DEFAULT_REVIEW_FORM_VALUES,
  );
  const [review, setReview] = useState<ArchitectureReviewResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [errorDetails, setErrorDetails] = useState<string[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleChange = (
    field: keyof ArchitectureReviewFormValues,
    value: string,
  ) => {
    setValues((current) => ({ ...current, [field]: value }));
  };

  const handleReset = () => {
    setValues(DEFAULT_REVIEW_FORM_VALUES);
    setReview(null);
    setErrorMessage(null);
    setErrorDetails([]);
  };

  const handleSubmit = async () => {
    const validation = validateReviewForm(values);
    if (!validation.ok) {
      setReview(null);
      setErrorMessage("Please fix the form before submitting.");
      setErrorDetails(validation.errors);
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);
    setErrorDetails([]);

    try {
      const result = await submitArchitectureReview(validation.value);
      setReview(result);
    } catch (error) {
      setReview(null);
      if (error instanceof ApiError) {
        setErrorMessage(error.message);
        setErrorDetails(error.details);
      } else {
        setErrorMessage(
          error instanceof Error
            ? error.message
            : "Unable to submit architecture review.",
        );
        setErrorDetails([]);
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="grid gap-6 xl:grid-cols-[minmax(320px,380px)_minmax(0,1fr)] xl:items-start">
      <ArchitectureReviewForm
        values={values}
        isSubmitting={isSubmitting}
        onChange={handleChange}
        onSubmit={() => {
          void handleSubmit();
        }}
        onReset={handleReset}
      />
      <ArchitectureReviewReport
        review={review}
        isLoading={isSubmitting}
        errorMessage={errorMessage}
        errorDetails={errorDetails}
      />
    </div>
  );
}
