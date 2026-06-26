import { describe, expect, it } from "vitest";

import { searchFormSchema } from "@/features/search/search-schema";

describe("searchFormSchema", () => {
  it("validates the backend search form fields", () => {
    const result = searchFormSchema.parse({
      industry: "Restaurants",
      country: "Nigeria",
      state: "Lagos",
      city: "Ikeja",
      perPage: "20"
    });

    expect(result.perPage).toBe(20);
  });

  it("rejects invalid per-page values", () => {
    expect(() =>
      searchFormSchema.parse({
        industry: "Restaurants",
        country: "Nigeria",
        state: "Lagos",
        city: "Ikeja",
        perPage: "101"
      })
    ).toThrow();
  });
});
