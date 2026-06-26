import { beforeEach, describe, expect, it, vi } from "vitest";

import { register, searchBusinesses } from "@/services/api-client";

describe("api client", () => {
  beforeEach(() => {
    document.cookie = "csrf_token=; Max-Age=0; path=/";
    vi.restoreAllMocks();
  });

  it("sends browser requests through the same-origin API proxy", async () => {
    document.cookie = "csrf_token=test-csrf";
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
      "/api/v1/search",
      expect.objectContaining({
        method: "POST",
        credentials: "include",
        body: expect.stringContaining("Restaurants")
      })
    );
    const headers = fetchMock.mock.calls[0][1].headers as Headers;
    expect(headers.get("X-CSRF-Token")).toBe("test-csrf");
  });

  it("bootstraps csrf before registration and calls the existing register route", async () => {
    const fetchMock = vi
      .fn()
      .mockImplementationOnce(async () => {
        document.cookie = "csrf_token=register-csrf";
        return {
          ok: true,
          status: 200,
          json: async () => ({
            success: true,
            data: {},
            message: null,
            request_id: "csrf-request"
          })
        };
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({
          success: true,
          data: {
            user: {
              id: "user-1",
              email: "founder@example.com",
              role: "user"
            }
          },
          message: null,
          request_id: "register-request"
        })
      });
    vi.stubGlobal("fetch", fetchMock);

    await register("founder@example.com", "StrongPassword1");

    expect(fetchMock).toHaveBeenNthCalledWith(
      1,
      "/api/v1/auth/csrf",
      expect.objectContaining({ credentials: "include" })
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      "/api/v1/auth/register",
      expect.objectContaining({
        method: "POST",
        credentials: "include",
        body: JSON.stringify({
          email: "founder@example.com",
          password: "StrongPassword1"
        })
      })
    );
    const headers = fetchMock.mock.calls[1][1].headers as Headers;
    expect(headers.get("X-CSRF-Token")).toBe("register-csrf");
  });

  it("logs url, status, and backend error details during development", async () => {
    document.cookie = "csrf_token=test-csrf";
    const consoleError = vi
      .spyOn(console, "error")
      .mockImplementation(() => undefined);
    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
      json: async () => ({
        success: false,
        error: {
          code: "SERVER_ERROR",
          message: "Backend failed."
        },
        request_id: "request-1"
      })
    });
    vi.stubGlobal("fetch", fetchMock);

    await expect(
      searchBusinesses({
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
      })
    ).rejects.toThrow("Backend failed.");

    expect(consoleError).toHaveBeenCalledWith(
      "[api-client] request failed",
      expect.objectContaining({
        url: "/api/v1/search",
        method: "POST",
        status: 500,
        payload: expect.objectContaining({
          error: expect.objectContaining({ message: "Backend failed." })
        })
      })
    );
  });
});
