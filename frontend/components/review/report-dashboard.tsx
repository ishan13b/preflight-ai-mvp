import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { ArchitectureReviewResponse } from "@/types/review";

type ReportDashboardProps = {
  review: ArchitectureReviewResponse;
};

export function ReportDashboard({ review }: ReportDashboardProps) {
  const metrics = [
    {
      label: "Overall Score",
      value: `${review.overall_score}`,
      hint: "/ 100",
    },
    {
      label: "Overall Status",
      value: review.overall_status,
    },
    {
      label: "Strengths",
      value: `${review.strengths.length}`,
    },
    {
      label: "Critical Risks",
      value: `${review.critical_risks.length}`,
    },
    {
      label: "Quick Wins",
      value: `${review.quick_wins.length}`,
    },
  ] as const;

  return (
    <Card>
      <CardHeader className="border-b">
        <CardTitle>Executive Summary</CardTitle>
        <CardDescription>{review.overall_summary}</CardDescription>
      </CardHeader>
      <CardContent className="pt-4">
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
          {metrics.map((metric) => (
            <div
              key={metric.label}
              className="rounded-lg border border-border/80 bg-muted/30 px-3 py-3"
            >
              <p className="text-[11px] font-medium tracking-wide text-muted-foreground uppercase">
                {metric.label}
              </p>
              <p className="mt-1 text-lg font-semibold tracking-tight text-foreground">
                {metric.value}
                {"hint" in metric && metric.hint ? (
                  <span className="ml-1 text-sm font-normal text-muted-foreground">
                    {metric.hint}
                  </span>
                ) : null}
              </p>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
