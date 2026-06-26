import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { SearchWorkspace } from "@/features/search/SearchWorkspace";
import { getJobStatus, searchBusinesses } from "@/services/api-client";

vi.mock("@/services/api-client", () => ({
  getJobStatus: vi.fn(),
  searchBusinesses: vi.fn(),
  userFriendlyError: () => "Friendly error"
}));

function renderWorkspace() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false }
    }
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <SearchWorkspace />
    </QueryClientProvider>
  );
}

describe("SearchWorkspace", () => {
  it("refreshes persisted businesses after a collection job completes", async () => {
    const user = userEvent.setup();
    vi.mocked(searchBusinesses)
      .mockResolvedValueOnce({
        results: [],
        pagination: {
          page: 1,
          per_page: 20,
          total: 0,
          total_pages: 0,
          has_next: false,
          has_previous: false
        },
        job: {
          id: "job-1",
          type: "contact_collection"
        }
      })
      .mockResolvedValueOnce({
        results: [
          {
            id: "business-1",
            name: "Worker Saved Bistro",
            industry: "Restaurants",
            phone: "+2348012345678",
            email: "hello@bistro.example",
            website: "https://bistro.example",
            country: "Nigeria",
            state: "Lagos",
            city: "Ikeja",
            address: "15 Allen Avenue, Ikeja",
            source_type: "osm"
          }
        ],
        pagination: {
          page: 1,
          per_page: 20,
          total: 1,
          total_pages: 1,
          has_next: false,
          has_previous: false
        },
        job: null
      });
    vi.mocked(getJobStatus).mockResolvedValue({
      id: "job-1",
      job_type: "contact_collection",
      status: "completed",
      attempts: 1,
      max_attempts: 3,
      dead_letter: false,
      dead_letter_reason: null,
      error_message: null
    });

    renderWorkspace();

    await user.click(screen.getByRole("button", { name: /^search$/i }));

    await waitFor(() => {
      expect(searchBusinesses).toHaveBeenCalledTimes(2);
    });
    expect(await screen.findByText("Worker Saved Bistro")).toBeInTheDocument();
    expect(screen.getByText("15 Allen Avenue, Ikeja")).toBeInTheDocument();
  });
});
