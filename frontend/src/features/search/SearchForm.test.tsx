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

    await user.clear(screen.getByLabelText("Industry"));
    await user.type(screen.getByLabelText("Industry"), "Clinics");
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
});
