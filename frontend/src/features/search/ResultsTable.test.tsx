import { render, screen } from "@testing-library/react";
import { createElement } from "react";
import { describe, expect, it, vi } from "vitest";

import { ResultsTable } from "@/features/search/ResultsTable";

const business = {
  id: "business-1",
  name: "Acme Clinic",
  industry: "Healthcare",
  phone: "+2348012345678",
  email: "hello@acme.example",
  website: "https://acme.example",
  country: "Nigeria",
  state: "Lagos",
  city: "Ikeja",
  address: "1 Main Street",
  source_type: "directory"
};

describe("ResultsTable", () => {
  it("renders returned businesses in the expected columns", () => {
    render(
      createElement(ResultsTable, {
        results: [business],
        pagination: {
          page: 1,
          per_page: 20,
          total: 1,
          total_pages: 1,
          has_next: false,
          has_previous: false
        },
        isLoading: false,
        onPageChange: vi.fn()
      })
    );

    expect(screen.getByText("Acme Clinic")).toBeInTheDocument();
    expect(screen.getByText("Healthcare")).toBeInTheDocument();
    expect(screen.getByText("hello@acme.example")).toBeInTheDocument();
    expect(screen.getByText("directory")).toBeInTheDocument();
  });
});
