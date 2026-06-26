"use client";

import { ExternalLink, Eye } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import type { BusinessSearchResult, Pagination } from "@/types/api";

type Props = {
  results: BusinessSearchResult[];
  pagination?: Pagination;
  isLoading: boolean;
  onPageChange: (page: number) => void;
};

export function ResultsTable({
  results,
  pagination,
  isLoading,
  onPageChange
}: Props) {
  if (isLoading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 6 }).map((_, index) => (
          <Skeleton key={index} className="h-12 w-full" />
        ))}
      </div>
    );
  }

  if (!results.length) {
    return (
      <div className="rounded-lg border border-dashed border-border p-8 text-center">
        <p className="text-sm font-medium">No businesses yet</p>
        <p className="mt-1 text-sm text-mutedForeground">
          Launch a collection job. Completed worker results will appear here.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="overflow-x-auto rounded-lg border border-border">
        <table className="w-full min-w-[980px] border-collapse text-left text-sm">
          <thead className="bg-secondary text-xs uppercase tracking-wide text-mutedForeground">
            <tr>
              {[
                "Business Name",
                "Industry",
                "Phone",
                "Email",
                "Website",
                "Address",
                "Source",
                "Actions"
              ].map((heading) => (
                <th key={heading} className="px-4 py-3 font-medium">
                  {heading}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {results.map((business) => (
              <tr
                key={business.id}
                className="border-t border-border hover:bg-secondary/40"
              >
                <td className="px-4 py-3 font-medium">{business.name}</td>
                <td className="px-4 py-3 text-mutedForeground">
                  {business.industry}
                </td>
                <td className="px-4 py-3">{business.phone || "-"}</td>
                <td className="px-4 py-3">{business.email ?? "-"}</td>
                <td className="px-4 py-3">
                  {business.website ? (
                    <a
                      className="inline-flex items-center gap-1 text-primary hover:underline"
                      href={business.website}
                      target="_blank"
                      rel="noreferrer"
                    >
                      Website
                      <ExternalLink className="h-3 w-3" />
                    </a>
                  ) : (
                    "-"
                  )}
                </td>
                <td className="px-4 py-3">{business.address}</td>
                <td className="px-4 py-3">{business.source_type}</td>
                <td className="px-4 py-3">
                  <Button
                    variant="ghost"
                    size="sm"
                    aria-label={`View ${business.name}`}
                  >
                    <Eye className="h-4 w-4" />
                    View
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {pagination ? (
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-sm text-mutedForeground">
            Page {pagination.page} of {pagination.total_pages || 1} -{" "}
            {pagination.total} results
          </p>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={!pagination.has_previous}
              onClick={() => onPageChange(pagination.page - 1)}
            >
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={!pagination.has_next}
              onClick={() => onPageChange(pagination.page + 1)}
            >
              Next
            </Button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
