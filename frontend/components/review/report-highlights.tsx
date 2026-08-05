import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { ArchitectureReviewResponse } from "@/types/review";

type ReportHighlightsProps = {
  review: ArchitectureReviewResponse;
};

export function ReportHighlights({ review }: ReportHighlightsProps) {
  return (
    <div className="grid gap-4 lg:grid-cols-3">
      <HighlightCard
        title="Strengths"
        description="Stable foundations already in place."
        emptyLabel="No notable strengths identified."
        items={review.strengths}
        marker="✓"
      />
      <HighlightCard
        title="Critical Risks"
        description="Gaps that block confident production rollout."
        emptyLabel="No critical risks flagged."
        items={review.critical_risks}
        marker="✗"
      />
      <HighlightCard
        title="Quick Wins"
        description="Highest-leverage actions to improve the score."
        emptyLabel="No quick wins suggested."
        items={review.quick_wins}
        ordered
      />
    </div>
  );
}

function HighlightCard({
  title,
  description,
  items,
  emptyLabel,
  marker,
  ordered = false,
}: {
  title: string;
  description: string;
  items: string[];
  emptyLabel: string;
  marker?: string;
  ordered?: boolean;
}) {
  return (
    <Card className="h-full">
      <CardHeader className="border-b">
        <CardTitle>{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent className="pt-4">
        {items.length === 0 ? (
          <p className="text-sm text-muted-foreground">{emptyLabel}</p>
        ) : ordered ? (
          <ol className="list-decimal space-y-2 pl-5 text-sm">
            {items.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ol>
        ) : (
          <ul className="space-y-2 text-sm">
            {items.map((item) => (
              <li key={item} className="flex gap-2">
                {marker ? (
                  <span className="mt-0.5 w-4 shrink-0 text-muted-foreground">
                    {marker}
                  </span>
                ) : null}
                <span>{item}</span>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
