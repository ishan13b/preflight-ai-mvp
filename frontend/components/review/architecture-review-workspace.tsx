"use client";

import { useEffect, useRef, useState } from "react";

import { ArchitectureReviewForm } from "@/components/review/architecture-review-form";
import { ArchitectureReviewReport } from "@/components/review/architecture-review-report";
import { BoardDecisionSummary } from "@/components/review/board-decision-summary";
import { ReviewBoard } from "@/components/review/review-board";
import { useReviewBoard } from "@/components/review/use-review-board";
import { ApiError } from "@/lib/errors";
import type { ExampleArchitecture } from "@/lib/exampleArchitectures";
import {
  EXAMPLE_HIGHLIGHT_DURATION_MS,
  scrollToArchitectureForm,
  toFormValuesFromExample,
} from "@/lib/load-example-architecture";
import { DEFAULT_REVIEW_FORM_VALUES } from "@/lib/review-form";
import { validateReviewForm } from "@/lib/validate-review-form";
import { submitArchitectureReview } from "@/services/review";
import type {
  ArchitectureReviewFormValues,
  ArchitectureReviewResponse,
} from "@/types/review";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

type ArchitectureReviewWorkspaceProps = {
  pendingExample?: ExampleArchitecture | null;
  exampleLoadToken?: number;
  onBusyChange?: (busy: boolean) => void;
};

export function ArchitectureReviewWorkspace({
  pendingExample = null,
  exampleLoadToken = 0,
  onBusyChange,
}: ArchitectureReviewWorkspaceProps) {
  const [values, setValues] = useState<ArchitectureReviewFormValues>(
    DEFAULT_REVIEW_FORM_VALUES,
  );
  const [review, setReview] = useState<ArchitectureReviewResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [errorDetails, setErrorDetails] = useState<string[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [sessionId, setSessionId] = useState(0);
  const [isHighlighted, setIsHighlighted] = useState(false);
  const [loadedExampleName, setLoadedExampleName] = useState<string | null>(
    null,
  );
  const highlightTimerRef = useRef<number | null>(null);

  const board = useReviewBoard({
    sessionId,
    review,
    errorMessage,
  });

  const isBusy = isSubmitting || board.phase === "reviewing";

  useEffect(() => {
    onBusyChange?.(isBusy);
  }, [isBusy, onBusyChange]);

  useEffect(() => {
    if (!pendingExample || exampleLoadToken === 0) {
      return;
    }

    setValues(toFormValuesFromExample(pendingExample));
    setLoadedExampleName(pendingExample.name);
    setReview(null);
    setErrorMessage(null);
    setErrorDetails([]);
    setIsSubmitting(false);
    setSessionId(0);
    setIsHighlighted(true);

    window.requestAnimationFrame(() => {
      scrollToArchitectureForm();
    });

    if (highlightTimerRef.current !== null) {
      window.clearTimeout(highlightTimerRef.current);
    }

    highlightTimerRef.current = window.setTimeout(() => {
      setIsHighlighted(false);
      highlightTimerRef.current = null;
    }, EXAMPLE_HIGHLIGHT_DURATION_MS);

    return () => {
      if (highlightTimerRef.current !== null) {
        window.clearTimeout(highlightTimerRef.current);
      }
    };
  }, [pendingExample, exampleLoadToken]);

  const handleChange = (
    field: keyof ArchitectureReviewFormValues,
    value: string,
  ) => {
    setValues((current) => ({ ...current, [field]: value }));
  };

  const handleReset = () => {
    setValues(DEFAULT_REVIEW_FORM_VALUES);
    setLoadedExampleName(null);
    setIsHighlighted(false);
    setReview(null);
    setErrorMessage(null);
    setErrorDetails([]);
    setIsSubmitting(false);
    setSessionId(0);
  };

  const handleSubmit = async () => {
    const validation = validateReviewForm(values);
    if (!validation.ok) {
      setReview(null);
      setErrorMessage("Please fix the form before submitting.");
      setErrorDetails(validation.errors);
      setSessionId(0);
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);
    setErrorDetails([]);
    setReview(null);
    setSessionId((current) => current + 1);

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
        isSubmitting={isBusy}
        isHighlighted={isHighlighted}
        loadedExampleName={loadedExampleName}
        onChange={handleChange}
        onSubmit={() => {
          void handleSubmit();
        }}
        onReset={handleReset}
      />

      <div className="space-y-4">
        <ReviewBoard members={board.members} isActive={board.isBoardActive} />

        {errorMessage ? (
          <Card>
            <CardHeader className="border-b">
              <CardTitle>Review Board</CardTitle>
              <CardDescription>
                The board could not complete this review cycle.
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-4">
              <div
                role="alert"
                className="rounded-lg border border-border bg-muted/40 px-4 py-3 text-sm"
              >
                <p className="font-medium text-foreground">{errorMessage}</p>
                {errorDetails.length > 0 ? (
                  <ul className="mt-2 list-disc space-y-1 pl-5 text-muted-foreground">
                    {errorDetails.map((detail) => (
                      <li key={detail}>{detail}</li>
                    ))}
                  </ul>
                ) : null}
              </div>
            </CardContent>
          </Card>
        ) : null}

        {board.phase === "awaiting_result" && !errorMessage ? (
          <Card>
            <CardHeader>
              <CardTitle>Finalizing Board Decision</CardTitle>
              <CardDescription>
                Reviewers are complete. Compiling the board summary…
              </CardDescription>
            </CardHeader>
          </Card>
        ) : null}

        {board.showBoardSummary && review ? (
          <BoardDecisionSummary review={review} />
        ) : null}

        {board.showDetailedReport && review ? (
          <ArchitectureReviewReport review={review} />
        ) : null}

        {!board.isBoardActive && !errorMessage && !review ? (
          <Card>
            <CardHeader className="border-b">
              <CardTitle>Awaiting Convening</CardTitle>
              <CardDescription>
                Load an example above or edit the form, then convene the Design
                Review Board (~3–5 seconds).
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-4">
              <p className="text-sm text-muted-foreground">
                Reviewers will move from Queued → Reviewing → Complete, cast
                votes, then reveal the detailed engineering report.
              </p>
            </CardContent>
          </Card>
        ) : null}
      </div>
    </div>
  );
}
