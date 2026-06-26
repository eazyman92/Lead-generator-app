import { beforeEach, describe, expect, it, vi } from "vitest";

import { searchBusinesses } from "@/services/api-client";

describe("api client", () => {
  beforeEach(() => {
    document.cookie = "csrf_token=test-csrf";
    vi.restoreAllMocks();
  });

  it("sends search requests with credentials and csrf headers", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        success: true,
        data: {
          results: [],
          pagination: {
            page: 1,
            per_page: 20,
            total: 0,
            total_pages: 0,
            has_next: false,
            has_previous: false
          },
          job: null
        },
        message: null,
        request_id: "request-1"
      })
    });
    vi.stubGlobal("fetch", fetchMock);

    await searchBusinesses({
      filters: {
        industry: "Restaurants",
        country: "Nigeria",
        state: "Lagos",
        city: "Ikeja"
      },
      pagination: {
        page: 1,
        per_page: 20
      }
    });

    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/search",
      expect.objectContaining({
        method: "POST",
        credentials: "include",
        body: expect.stringContaining("Restaurants")
      })
    );
    const headers = fetchMock.mock.calls[0][1].headers as Headers;
    expect(headers.get("X-CSRF-Token")).toBe("test-csrf");
  });
});
