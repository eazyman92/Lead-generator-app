"use client";

import { Check, ChevronDown, Search } from "lucide-react";
import { useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { cn } from "@/utils/cn";

export type ComboboxOption = {
  label: string;
  value: string;
  meta?: string;
};

type Props = {
  id?: string;
  options: ComboboxOption[];
  value: string;
  placeholder: string;
  emptyMessage?: string;
  disabled?: boolean;
  onChange: (value: string) => void;
};

export function Combobox({
  id,
  options,
  value,
  placeholder,
  emptyMessage = "No matches found.",
  disabled = false,
  onChange
}: Props) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const selected = options.find((option) => option.value === value);
  const filtered = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    if (!normalized) {
      return options;
    }
    return options.filter((option) =>
      `${option.label} ${option.meta ?? ""}`.toLowerCase().includes(normalized)
    );
  }, [options, query]);

  return (
    <div className="relative">
      <Button
        id={id}
        type="button"
        variant="outline"
        className={cn(
          "h-10 w-full justify-between bg-input px-3 text-left font-normal",
          !selected && "text-mutedForeground"
        )}
        disabled={disabled}
        aria-haspopup="listbox"
        aria-expanded={open}
        onClick={() => setOpen((current) => !current)}
      >
        <span className="truncate">{selected?.label ?? placeholder}</span>
        <ChevronDown className="h-4 w-4 shrink-0 text-mutedForeground" />
      </Button>

      {open ? (
        <div className="absolute z-30 mt-2 w-full rounded-md border border-border bg-card p-2 shadow-xl">
          <div className="relative mb-2">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted" />
            <input
              className="h-9 w-full rounded-md border border-border bg-background pl-9 pr-3 text-sm text-foreground outline-none focus:ring-2 focus:ring-ring"
              placeholder="Search..."
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              autoFocus
            />
          </div>
          <div className="max-h-60 overflow-y-auto" role="listbox">
            {filtered.length ? (
              filtered.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  role="option"
                  aria-selected={option.value === value}
                  className={cn(
                    "flex w-full items-center justify-between rounded-md px-3 py-2 text-left text-sm",
                    "hover:bg-secondary",
                    option.value === value && "bg-secondary text-foreground"
                  )}
                  onClick={() => {
                    onChange(option.value);
                    setOpen(false);
                    setQuery("");
                  }}
                >
                  <span className="min-w-0">
                    <span className="block truncate">{option.label}</span>
                    {option.meta ? (
                      <span className="block truncate text-xs text-mutedForeground">
                        {option.meta}
                      </span>
                    ) : null}
                  </span>
                  {option.value === value ? (
                    <Check className="h-4 w-4 shrink-0 text-primary" />
                  ) : null}
                </button>
              ))
            ) : (
              <p className="px-3 py-2 text-sm text-mutedForeground">
                {emptyMessage}
              </p>
            )}
          </div>
        </div>
      ) : null}
    </div>
  );
}
