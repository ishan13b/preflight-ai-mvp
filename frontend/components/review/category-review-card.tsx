import type { ReactNode } from "react";

import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { severityBadgeVariant } from "@/lib/severity";
import type { CategoryReview } from "@/types/review";

type CategoryReviewCardProps = {
  category: CategoryReview;
};

export function CategoryReviewCard({ category }: CategoryReviewCardProps) {
  return (
    <Card>
      <CardHeader className="border-b">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0 space-y-1">
            <CardTitle>{category.category}</CardTitle>
            <CardDescription>{category.summary}</CardDescription>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="outline" className="rounded-md font-normal">
              Score {category.score}/10
            </Badge>
            <Badge variant="secondary" className="rounded-md font-normal">
              Confidence {category.confidence}%
            </Badge>
            <Badge
              variant={severityBadgeVariant(category.severity)}
              className="rounded-md font-normal tracking-wide"
            >
              {category.severity}
            </Badge>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-5 pt-4">
        <Section title="Engineering Reasoning">
          <p className="text-sm leading-relaxed text-foreground/90">
            {category.engineering_reasoning}
          </p>
        </Section>

        <Section title="Estimated Impact">
          <p className="text-sm leading-relaxed text-foreground/90">
            {category.estimated_impact}
          </p>
        </Section>

        <div className="grid gap-5 md:grid-cols-2">
          <ItemList
            title="Issues"
            items={category.issues}
            emptyLabel="No issues detected."
          />
          <ItemList
            title="Recommendations"
            items={category.recommendations}
            emptyLabel="No recommendations."
          />
        </div>
      </CardContent>
    </Card>
  );
}

function Section({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <div>
      <h4 className="text-[11px] font-medium tracking-wide text-muted-foreground uppercase">
        {title}
      </h4>
      <div className="mt-2">{children}</div>
    </div>
  );
}

function ItemList({
  title,
  items,
  emptyLabel,
}: {
  title: string;
  items: string[];
  emptyLabel: string;
}) {
  return (
    <Section title={title}>
      {items.length === 0 ? (
        <p className="text-sm text-muted-foreground">{emptyLabel}</p>
      ) : (
        <ul className="list-disc space-y-1.5 pl-5 text-sm">
          {items.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      )}
    </Section>
  );
}
