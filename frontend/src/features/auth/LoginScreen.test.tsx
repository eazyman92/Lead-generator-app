import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { LoginScreen } from "@/features/auth/LoginScreen";
import { register } from "@/services/api-client";

const replace = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    replace
  })
}));

vi.mock("@/services/api-client", () => ({
  login: vi.fn(),
  register: vi.fn(),
  userFriendlyError: () => "Friendly error"
}));

function renderLoginScreen() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false }
    }
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <LoginScreen />
    </QueryClientProvider>
  );
}

describe("LoginScreen", () => {
  it("connects account creation to the existing registration flow", async () => {
    const user = userEvent.setup();
    vi.mocked(register).mockResolvedValue({
      id: "user-1",
      email: "founder@example.com",
      role: "user"
    });

    renderLoginScreen();

    await user.click(
      screen.getByRole("button", { name: /create a new account/i })
    );
    await user.type(screen.getByLabelText(/email/i), "founder@example.com");
    await user.type(screen.getByLabelText(/password/i), "StrongPassword1");
    await user.click(screen.getByRole("button", { name: /^create account$/i }));

    await waitFor(() => {
      expect(register).toHaveBeenCalledWith(
        "founder@example.com",
        "StrongPassword1"
      );
    });
    expect(replace).toHaveBeenCalledWith("/");
  });
});
