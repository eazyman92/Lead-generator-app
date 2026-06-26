"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Search } from "lucide-react";
import { useForm } from "react-hook-form";
import type { z } from "zod";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Spinner } from "@/components/ui/spinner";
import {
  searchFormSchema,
  type SearchFormValues
} from "@/features/search/search-schema";

type Props = {
  isSearching: boolean;
  onSubmit: (values: SearchFormValues) => void;
};

export function SearchForm({ isSearching, onSubmit }: Props) {
  const form = useForm<
    z.input<typeof searchFormSchema>,
    unknown,
    SearchFormValues
  >({
    resolver: zodResolver(searchFormSchema),
    defaultValues: {
      industry: "Restaurants",
      country: "Nigeria",
      state: "Lagos",
      city: "Ikeja",
      perPage: 20
    }
  });

  return (
    <form
      className="grid gap-4 lg:grid-cols-[repeat(4,minmax(0,1fr))_140px_auto]"
      onSubmit={form.handleSubmit(onSubmit)}
    >
      <Field label="Industry" error={form.formState.errors.industry?.message}>
        <Input placeholder="Restaurants" {...form.register("industry")} />
      </Field>
      <Field label="Country" error={form.formState.errors.country?.message}>
        <Input placeholder="Nigeria" {...form.register("country")} />
      </Field>
      <Field label="State" error={form.formState.errors.state?.message}>
        <Input placeholder="Lagos" {...form.register("state")} />
      </Field>
      <Field label="City" error={form.formState.errors.city?.message}>
        <Input placeholder="Ikeja" {...form.register("city")} />
      </Field>
      <Field label="Results" error={form.formState.errors.perPage?.message}>
        <Select {...form.register("perPage")}>
          {[10, 20, 25, 50, 100].map((value) => (
            <option key={value} value={value}>
              {value}
            </option>
          ))}
        </Select>
      </Field>
      <div className="flex items-end">
        <Button className="w-full" type="submit" disabled={isSearching}>
          {isSearching ? <Spinner /> : <Search className="h-4 w-4" />}
          Search
        </Button>
      </div>
    </form>
  );
}

function Field({
  label,
  error,
  children
}: {
  label: string;
  error?: string;
  children: React.ReactNode;
}) {
  return (
    <label className="block space-y-2">
      <span className="text-sm text-mutedForeground">{label}</span>
      {children}
      {error ? <span className="text-xs text-destructive">{error}</span> : null}
    </label>
  );
}
