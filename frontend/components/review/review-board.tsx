"use client";

import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { boardVoteTone } from "@/lib/board";
import { cn } from "@/lib/utils";
import type { BoardVote, ReviewerBoardStatus } from "@/types/review";

export type BoardMemberState = {
  name: string;
  status: ReviewerBoardStatus;
  vote?: BoardVote;
  score?: number;
};

type ReviewBoardProps = {
  members: BoardMemberState[];
  isActive: boolean;
};

export function ReviewBoard({ members, isActive }: ReviewBoardProps) {
  const completed = members.filter((member) => member.status === "complete").length;
  const progressValue = members.length
    ? Math.round((completed / members.length) * 100)
    : 0;

  return (
    <Card>
      <CardHeader className="border-b">
        <CardTitle>AI Design Review Board</CardTitle>
        <CardDescription>
          {isActive
            ? "Reviewers are evaluating the architecture in sequence."
            : "Submit an architecture to convene the board."}
        </CardDescription>
        {isActive ? (
          <div className="pt-3">
            <Progress value={progressValue} className="w-full">
              <div className="flex w-full items-center justify-between text-xs text-muted-foreground">
                <span>
                  {completed}/{members.length} complete
                </span>
                <span>{progressValue}%</span>
              </div>
            </Progress>
          </div>
        ) : null}
      </CardHeader>
      <CardContent className="pt-4">
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
          {members.map((member) => (
            <ReviewerStatusCard key={member.name} member={member} />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

function ReviewerStatusCard({ member }: { member: BoardMemberState }) {
  const statusLabel =
    member.status === "queued"
      ? "Queued"
      : member.status === "reviewing"
        ? "Reviewing..."
        : "Complete";

  return (
    <div
      className={cn(
        "rounded-lg border border-border/80 bg-background px-3 py-3 transition-colors",
        member.status === "reviewing" && "border-foreground/25 bg-muted/40",
        member.status === "complete" && "bg-muted/20",
      )}
    >
      <div className="flex items-start justify-between gap-2">
        <p className="text-sm font-medium tracking-tight">{member.name}</p>
        <Badge
          variant={member.status === "complete" ? "secondary" : "outline"}
          className="rounded-md font-normal"
        >
          {statusLabel}
        </Badge>
      </div>

      {member.status === "reviewing" ? (
        <div className="mt-3">
          <Progress value={66} className="w-full" />
        </div>
      ) : null}

      {member.status === "complete" && member.vote ? (
        <div className="mt-3 space-y-1">
          <p
            className={cn(
              "text-xs font-medium tracking-wide",
              boardVoteTone(member.vote) === "positive" && "text-foreground",
              boardVoteTone(member.vote) === "warning" && "text-muted-foreground",
              boardVoteTone(member.vote) === "negative" && "text-foreground",
            )}
          >
            {member.vote}
          </p>
          {typeof member.score === "number" ? (
            <p className="text-xs text-muted-foreground tabular-nums">
              Score {member.score}/10
            </p>
          ) : null}
        </div>
      ) : (
        <p className="mt-3 text-xs text-muted-foreground">
          {member.status === "queued"
            ? "Waiting for prior reviewers."
            : "Inspecting architecture signals…"}
        </p>
      )}
    </div>
  );
}
