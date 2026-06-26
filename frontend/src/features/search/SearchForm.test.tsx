import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createElement } from "react";
import { describe, expect, it, vi } from "vitest";

import { SearchForm } from "@/features/search/SearchForm";

describe("SearchForm", () => {
  it("submits values using the backend search schema fields", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();

    render(createElement(SearchForm, { isSearching: false, onSubmit }));

    await user.click(screen.getByRole("button", { name: /industry/i }));
    await user.type(screen.getByPlaceholderText("Search..."), "Clinics");
    await user.click(screen.getByRole("option", { name: /clinics/i }));
    await user.click(screen.getByRole("button", { name: /search/i }));

    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({
        industry: "Clinics",
        country: "Nigeria",
        state: "Lagos",
        city: "Ikeja",
        perPage: 20
      }),
      expect.anything()
    );
  });

  it("cascades states and cities from the selected country", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();

    render(createElement(SearchForm, { isSearching: false, onSubmit }));

    await user.click(screen.getByRole("button", { name: /country/i }));
    await user.type(screen.getByPlaceholderText("Search..."), "United States");
    await user.click(screen.getByRole("option", { name: /united states/i }));

    expect(screen.getByText("California")).toBeInTheDocument();
    expect(screen.getByText("Los Angeles")).toBeInTheDocument();
  });
});
