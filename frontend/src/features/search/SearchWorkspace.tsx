"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Database, Search, ShieldCheck, Sparkles } from "lucide-react";
import { useEffect, useState } from "react";
import { toast } from "sonner";

import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { JobStatusPanel } from "@/features/search/JobStatusPanel";
import { ResultsTable } from "@/features/search/ResultsTable";
import { SearchForm } from "@/features/search/SearchForm";
import type { SearchFormValues } from "@/features/search/search-schema";
import {
  getJobStatus,
  searchBusinesses,
  userFriendlyError
} from "@/services/api-client";
import type {
  BusinessSearchResponse,
  JobStage,
  SearchPayload
} from "@/types/api";

function buildPayload(values: SearchFormValues, page: number): SearchPayload {
  return {
    filters: {
      industry: values.industry,
      country: values.country,
      state: values.state,
      city: values.city
    },
    pagination: {
      page,
      per_page: values.perPage
    }
  };
}

export function SearchWorkspace() {
  const [lastValues, setLastValues] = useState<SearchFormValues | null>(null);
  const [page, setPage] = useState(1);
  const [jobStage, setJobStage] = useState<JobStage>("idle");
  const [searchData, setSearchData] = useState<BusinessSearchResponse | null>(
    null
  );
  const [jobStatusMessage, setJobStatusMessage] = useState<
    string | undefined
  >();
  const [refreshedJobId, setRefreshedJobId] = useState<string | null>(null);

  const jobId = searchData?.job?.id;
  const jobStatusQuery = useQuery({
    queryKey: ["job-status", jobId],
    queryFn: () => getJobStatus(jobId as string),
    enabled:
      Boolean(jobId) && jobStage !== "completed" && jobStage !== "failed",
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status === "completed" || status === "failed") {
        return false;
      }
      return 2500;
    }
  });

  const searchMutation = useMutation({
    mutationFn: (payload: SearchPayload) => searchBusinesses(payload),
    onMutate: () => {
      setJobStage("created");
      setJobStatusMessage("Background contact collection job queued.");
      setRefreshedJobId(null);
      toast.info("Search started.");
    },
    onSuccess: (data) => {
      setSearchData(data);
      setJobStage(data.job ? "processing" : "completed");
      setJobStatusMessage(
        data.job ? undefined : "Search completed. Job metadata unavailable."
      );
      toast.success("Search completed.");
    },
    onError: (error) => {
      setJobStage("failed");
      setJobStatusMessage(userFriendlyError(error));
      toast.error(userFriendlyError(error));
    }
  });
  const refreshResultsMutation = useMutation({
    mutationFn: (payload: SearchPayload) => searchBusinesses(payload),
    onSuccess: (data) => {
      setSearchData(data);
      setJobStage("completed");
      setJobStatusMessage("Contact collection completed. Results refreshed.");
      toast.success("Collected businesses are ready.");
    },
    onError: (error) => {
      setJobStatusMessage(userFriendlyError(error));
      toast.error(userFriendlyError(error));
    }
  });

  const jobStatus = jobStatusQuery.data;
  useEffect(() => {
    if (jobStatus?.status === "completed") {
      setJobStage("completed");
      setJobStatusMessage("Contact collection completed.");
      if (lastValues && jobId && refreshedJobId !== jobId) {
        setRefreshedJobId(jobId);
        refreshResultsMutation.mutate(buildPayload(lastValues, page));
      }
    }
    if (jobStatus?.status === "failed") {
      setJobStage("failed");
      setJobStatusMessage(
        jobStatus.error_message ?? jobStatus.dead_letter_reason ?? "Job failed."
      );
    }
    if (jobStatusQuery.error) {
      setJobStatusMessage(userFriendlyError(jobStatusQuery.error));
    }
  }, [
    jobId,
    jobStatus,
    jobStatusQuery.error,
    lastValues,
    page,
    refreshedJobId,
    refreshResultsMutation
  ]);

  function submit(values: SearchFormValues) {
    setLastValues(values);
    setPage(1);
    searchMutation.mutate(buildPayload(values, 1));
  }

  function changePage(nextPage: number) {
    if (!lastValues) {
      return;
    }
    setPage(nextPage);
    searchMutation.mutate(buildPayload(lastValues, nextPage));
  }

  return (
    <div className="mx-auto max-w-7xl space-y-6 px-4 py-6 sm:px-6">
      <motion.section
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="grid gap-4 lg:grid-cols-3"
      >
        {[
          { label: "Workflow", value: "Search to Leads", icon: Search },
          { label: "Security", value: "Protected Session", icon: ShieldCheck },
          { label: "Collection", value: "Worker Pipeline", icon: Database }
        ].map((item) => (
          <Card key={item.label} className="bg-card/70">
            <CardContent className="flex items-center justify-between">
              <div>
                <p className="text-sm text-mutedForeground">{item.label}</p>
                <p className="mt-1 text-xl font-semibold">{item.value}</p>
              </div>
              <item.icon className="h-5 w-5 text-primary" />
            </CardContent>
          </Card>
        ))}
      </motion.section>

      <Card>
        <CardHeader>
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="flex items-center gap-2 text-sm text-primary">
                <Sparkles className="h-4 w-4" />
                Live acquisition workspace
              </p>
              <h2 className="mt-1 text-2xl font-semibold">
                Build a verified business list
              </h2>
              <p className="mt-2 max-w-2xl text-sm text-mutedForeground">
                Choose an industry and location, launch collection, and review
                businesses saved by the worker as soon as processing completes.
              </p>
            </div>
            <JobStatusPanel
              stage={jobStage}
              status={jobStatus}
              message={jobStatusMessage}
            />
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          <SearchForm
            isSearching={searchMutation.isPending}
            onSubmit={submit}
          />
          <ResultsTable
            results={searchData?.results ?? []}
            pagination={searchData?.pagination}
            isLoading={searchMutation.isPending || refreshResultsMutation.isPending}
            onPageChange={changePage}
          />
        </CardContent>
      </Card>
    </div>
  );
}
