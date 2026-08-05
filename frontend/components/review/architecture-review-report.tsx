import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { CategoryReviewCard } from "@/components/review/category-review-card";
import { ReportDashboard } from "@/components/review/report-dashboard";
import { ReportHighlights } from "@/components/review/report-highlights";
import type { ArchitectureReviewResponse } from "@/types/review";

type ArchitectureReviewReportProps = {
  review: ArchitectureReviewResponse | null;
  isLoading: boolean;
  errorMessage: string | null;
  errorDetails: string[];
};

export function ArchitectureReviewReport({
  review,
  isLoading,
  errorMessage,
  errorDetails,
}: ArchitectureReviewReportProps) {
  if (isLoading) {
    return (
      <StatusCard
        title="Architecture Review"
        description="Generating a consultancy-style engineering report…"
      />
    );
  }

  if (errorMessage) {
    return (
      <Card>
        <CardHeader className="border-b">
          <CardTitle>Architecture Review</CardTitle>
          <CardDescription>
            The report could not be generated for this submission.
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
    );
  }

  if (!review) {
    return (
      <StatusCard
        title="Architecture Review"
        description="Submit an architecture on the left to generate a structured engineering report."
      />
    );
  }

  return (
    <div className="space-y-4">
      <ReportDashboard review={review} />
      <ReportHighlights review={review} />
      <div className="space-y-4">
        {review.categories.map((category) => (
          <CategoryReviewCard key={category.category} category={category} />
        ))}
      </div>
    </div>
  );
}

function StatusCard({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <Card className="h-full min-h-64">
      <CardHeader className="border-b">
        <CardTitle>{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent className="pt-4">
        <p className="text-sm text-muted-foreground">
          Reports include score, severity, reasoning, and prioritized actions.
        </p>
      </CardContent>
    </Card>
  );
}
