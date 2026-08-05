import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { ArchitectureReviewResponse } from "@/types/review";

type BoardDecisionSummaryProps = {
  review: ArchitectureReviewResponse;
};

export function BoardDecisionSummary({ review }: BoardDecisionSummaryProps) {
  return (
    <Card>
      <CardHeader className="border-b">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <CardTitle>Review Board Summary</CardTitle>
            <CardDescription className="mt-1">{review.board_summary}</CardDescription>
          </div>
          <Badge variant="outline" className="rounded-md px-3 py-1 font-medium tracking-wide">
            {review.final_decision}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="pt-4">
        <div className="grid gap-3 sm:grid-cols-3">
          <Metric label="Final Decision" value={review.final_decision} />
          <Metric
            label="Overall Score"
            value={`${review.overall_score}`}
            hint="/ 100"
          />
          <Metric label="Overall Status" value={review.overall_status} />
        </div>

        <div className="mt-5 overflow-hidden rounded-lg border border-border/80">
          <div className="grid grid-cols-[1.2fr_0.6fr_1.4fr] gap-2 border-b bg-muted/40 px-3 py-2 text-[11px] font-medium tracking-wide text-muted-foreground uppercase">
            <span>Reviewer</span>
            <span>Score</span>
            <span>Vote</span>
          </div>
          {review.reviewer_votes.map((vote) => (
            <div
              key={vote.reviewer}
              className="grid grid-cols-[1.2fr_0.6fr_1.4fr] gap-2 border-b border-border/60 px-3 py-2.5 text-sm last:border-b-0"
            >
              <span className="font-medium">{vote.reviewer}</span>
              <span className="tabular-nums text-muted-foreground">
                {vote.score}/10
              </span>
              <span>{vote.vote}</span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

function Metric({
  label,
  value,
  hint,
}: {
  label: string;
  value: string;
  hint?: string;
}) {
  return (
    <div className="rounded-lg border border-border/80 bg-muted/30 px-3 py-3">
      <p className="text-[11px] font-medium tracking-wide text-muted-foreground uppercase">
        {label}
      </p>
      <p className="mt-1 text-base font-semibold tracking-tight">
        {value}
        {hint ? (
          <span className="ml-1 text-sm font-normal text-muted-foreground">{hint}</span>
        ) : null}
      </p>
    </div>
  );
}
