"use client";

import { CheckCircle2, CircleDashed, Clock3, XCircle } from "lucide-react";

import type { JobStage, JobStatus } from "@/types/api";
import { cn } from "@/utils/cn";

type Props = {
  stage: JobStage;
  status?: JobStatus;
  message?: string;
};

const stageConfig = {
  idle: { icon: CircleDashed, label: "Ready", tone: "text-mutedForeground" },
  created: { icon: Clock3, label: "Job created", tone: "text-primary" },
  processing: { icon: CircleDashed, label: "Processing", tone: "text-primary" },
  completed: { icon: CheckCircle2, label: "Completed", tone: "text-primary" },
  failed: { icon: XCircle, label: "Failed", tone: "text-destructive" }
};

export function JobStatusPanel({ stage, status, message }: Props) {
  const config = stageConfig[stage];
  const Icon = config.icon;
  const detail =
    message ??
    (status
      ? `${status.job_type} / ${status.status} / attempt ${status.attempts}/${status.max_attempts}`
      : "Search jobs are created automatically when a search is submitted.");

  return (
    <div
      className={cn(
        "flex flex-col gap-3 rounded-lg border border-border bg-secondary/40 p-4",
        "sm:flex-row sm:items-center sm:justify-between"
      )}
    >
      <div className="flex items-center gap-3">
        <Icon
          className={cn(
            "h-5 w-5",
            stage === "processing" && "animate-spin",
            config.tone
          )}
        />
        <div>
          <p className="text-sm font-medium">{config.label}</p>
          <p className="text-xs text-mutedForeground">{detail}</p>
        </div>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-background sm:w-48">
        <div
          className={cn(
            "h-full rounded-full bg-primary transition-all",
            stage === "idle" && "w-1/12",
            stage === "created" && "w-1/3",
            stage === "processing" && "w-2/3",
            stage === "completed" && "w-full",
            stage === "failed" && "w-full bg-destructive"
          )}
        />
      </div>
    </div>
  );
}
