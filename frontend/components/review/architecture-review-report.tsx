import { CategoryReviewCard } from "@/components/review/category-review-card";
import { ReportDashboard } from "@/components/review/report-dashboard";
import { ReportHighlights } from "@/components/review/report-highlights";
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { ArchitectureReviewResponse } from "@/types/review";

type ArchitectureReviewReportProps = {
  review: ArchitectureReviewResponse;
};

export function ArchitectureReviewReport({
  review,
}: ArchitectureReviewReportProps) {
  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="border-b">
          <CardTitle>Detailed Engineering Report</CardTitle>
          <CardDescription>
            Full findings from each board discipline after the vote tally.
          </CardDescription>
        </CardHeader>
      </Card>

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
