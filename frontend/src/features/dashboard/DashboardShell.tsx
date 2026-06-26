"use client";

import { useQuery } from "@tanstack/react-query";
import {
  BarChart3,
  Building2,
  CheckCircle2,
  ChevronRight,
  LogOut,
  Menu,
  Search,
  Settings,
  ShieldCheck,
  Sparkles
} from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { SearchWorkspace } from "@/features/search/SearchWorkspace";
import {
  getCurrentUser,
  logout,
  userFriendlyError
} from "@/services/api-client";
import { cn } from "@/utils/cn";

const navItems = [
  { label: "Search", icon: Search, active: true, enabled: true },
  { label: "Businesses", icon: Building2, active: false, enabled: false },
  { label: "Reports", icon: BarChart3, active: false, enabled: false },
  { label: "Security", icon: ShieldCheck, active: false, enabled: false },
  { label: "Settings", icon: Settings, active: false, enabled: false }
];

export function DashboardShell() {
  const router = useRouter();
  const [profileOpen, setProfileOpen] = useState(false);
  const {
    data: user,
    isLoading,
    error
  } = useQuery({
    queryKey: ["auth", "me"],
    queryFn: getCurrentUser,
    retry: false
  });

  useEffect(() => {
    if (error) {
      toast.error(userFriendlyError(error));
      router.replace("/login");
    }
  }, [error, router]);

  if (isLoading) {
    return (
      <main className="flex min-h-screen items-center justify-center p-6">
        <div className="w-full max-w-5xl space-y-4">
          <Skeleton className="h-12 w-56" />
          <Skeleton className="h-80 w-full" />
        </div>
      </main>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <main className="min-h-screen text-foreground">
      <div className="grid min-h-screen grid-cols-1 lg:grid-cols-[260px_1fr]">
        <aside className="hidden border-r border-border bg-background/70 p-4 backdrop-blur lg:block">
          <div className="mb-8 flex items-center gap-3 px-2">
            <div
              className={cn(
                "flex h-10 w-10 items-center justify-center rounded-md",
                "bg-primary text-primaryForeground"
              )}
            >
              <Sparkles className="h-5 w-5" />
            </div>
            <div>
              <p className="text-sm text-mutedForeground">Lead Generator App</p>
              <h1 className="font-semibold">Acquisition Console</h1>
            </div>
          </div>

          <nav className="space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <button
                  key={item.label}
                  disabled={!item.enabled}
                  className={cn(
                    "flex h-10 w-full items-center justify-between rounded-md px-3 text-sm",
                    "transition",
                    item.active
                      ? "bg-secondary text-foreground"
                      : item.enabled
                        ? "text-mutedForeground hover:bg-secondary hover:text-foreground"
                        : "cursor-not-allowed text-mutedForeground/45"
                  )}
                  type="button"
                >
                  <span className="flex items-center gap-3">
                    <Icon className="h-4 w-4" />
                    {item.label}
                  </span>
                  {item.active ? <ChevronRight className="h-4 w-4" /> : null}
                  {!item.enabled ? (
                    <span className="rounded-full border border-border px-2 py-0.5 text-[10px] uppercase tracking-wide">
                      Soon
                    </span>
                  ) : null}
                </button>
              );
            })}
          </nav>
        </aside>

        <section className="min-w-0">
          <header className="sticky top-0 z-20 border-b border-border bg-background/80 backdrop-blur">
            <div className="flex h-16 items-center justify-between gap-3 px-4 sm:px-6">
              <div className="flex items-center gap-3">
                <Button
                  variant="ghost"
                  size="icon"
                  className="lg:hidden"
                  aria-label="Open navigation"
                >
                  <Menu className="h-5 w-5" />
                </Button>
                <div>
                  <p className="text-xs uppercase tracking-[0.18em] text-mutedForeground">
                    Phase 5B
                  </p>
                  <h2 className="text-base font-semibold">
                    Production Search Experience
                  </h2>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="hidden items-center gap-2 rounded-full border border-border px-3 py-1.5 text-xs text-mutedForeground sm:flex">
                  <CheckCircle2 className="h-3.5 w-3.5 text-primary" />
                  Secure session
                </div>
                <div className="relative">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setProfileOpen((current) => !current)}
                  >
                    <span className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-xs font-semibold text-primaryForeground">
                      {user.email.slice(0, 1).toUpperCase()}
                    </span>
                    Account
                  </Button>
                  {profileOpen ? (
                    <div className="absolute right-0 z-30 mt-2 w-72 rounded-md border border-border bg-card p-3 shadow-xl">
                      <div className="border-b border-border pb-3">
                        <p className="text-sm font-medium">{user.email}</p>
                        <p className="mt-1 text-xs text-mutedForeground">
                          {user.role} account - cookie-authenticated
                        </p>
                      </div>
                      <Button
                        variant="ghost"
                        className="mt-3 w-full justify-start"
                        onClick={async () => {
                          await logout();
                          toast.success("Signed out.");
                          router.replace("/login");
                        }}
                      >
                        <LogOut className="h-4 w-4" />
                        Sign out
                      </Button>
                    </div>
                  ) : null}
                </div>
              </div>
            </div>
          </header>

          <SearchWorkspace />
        </section>
      </div>
    </main>
  );
}
