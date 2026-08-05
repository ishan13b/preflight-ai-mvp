import type { VariantProps } from "class-variance-authority";

import { badgeVariants } from "@/components/ui/badge";
import type { Severity } from "@/types/review";

type BadgeVariant = NonNullable<VariantProps<typeof badgeVariants>["variant"]>;

/** Map severity to a restrained badge variant for consultancy-style UI. */
export function severityBadgeVariant(severity: Severity): BadgeVariant {
  switch (severity) {
    case "CRITICAL":
      return "destructive";
    case "HIGH":
      return "outline";
    case "MEDIUM":
      return "secondary";
    case "LOW":
    default:
      return "secondary";
  }
}
