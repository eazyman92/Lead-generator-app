"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Search } from "lucide-react";
import { Controller, useForm } from "react-hook-form";
import type { z } from "zod";

import { Button } from "@/components/ui/button";
import { Combobox } from "@/components/ui/combobox";
import { Select } from "@/components/ui/select";
import { Spinner } from "@/components/ui/spinner";
import {
  countries,
  getCountry,
  getState,
  industryOptions
} from "@/data/search-options";
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
  const selectedCountry = form.watch("country");
  const selectedState = form.watch("state");
  const country = getCountry(selectedCountry);
  const state = getState(selectedCountry, selectedState);
  const countryOptions = countries.map((item) => ({
    label: item.name,
    value: item.name,
    meta: `${item.iso2} / ${item.iso3}`
  }));
  const stateOptions =
    country?.states.map((item) => ({
      label: item.name,
      value: item.name,
      meta: item.code
    })) ?? [];
  const cityOptions =
    state?.cities.map((item) => ({
      label: item.name,
      value: item.name
    })) ?? [];

  return (
    <form
      className="grid gap-4 lg:grid-cols-[repeat(4,minmax(0,1fr))_140px_auto]"
      onSubmit={form.handleSubmit(onSubmit)}
    >
      <Field label="Industry" error={form.formState.errors.industry?.message}>
        <Controller
          control={form.control}
          name="industry"
          render={({ field }) => (
            <Combobox
              options={industryOptions.map((industry) => ({
                label: industry,
                value: industry
              }))}
              value={field.value}
              placeholder="Choose industry"
              onChange={field.onChange}
            />
          )}
        />
      </Field>
      <Field label="Country" error={form.formState.errors.country?.message}>
        <Controller
          control={form.control}
          name="country"
          render={({ field }) => (
            <Combobox
              options={countryOptions}
              value={field.value}
              placeholder="Choose country"
              onChange={(value) => {
                field.onChange(value);
                const nextCountry = getCountry(value);
                const nextState = nextCountry?.states[0];
                form.setValue("state", nextState?.name ?? "", {
                  shouldValidate: true
                });
                form.setValue("city", nextState?.cities[0]?.name ?? "", {
                  shouldValidate: true
                });
              }}
            />
          )}
        />
      </Field>
      <Field label="State" error={form.formState.errors.state?.message}>
        <Controller
          control={form.control}
          name="state"
          render={({ field }) => (
            <Combobox
              options={stateOptions}
              value={field.value}
              placeholder="Choose state"
              disabled={!country}
              onChange={(value) => {
                field.onChange(value);
                const nextState = getState(selectedCountry, value);
                form.setValue("city", nextState?.cities[0]?.name ?? "", {
                  shouldValidate: true
                });
              }}
            />
          )}
        />
      </Field>
      <Field label="City" error={form.formState.errors.city?.message}>
        <Controller
          control={form.control}
          name="city"
          render={({ field }) => (
            <Combobox
              options={cityOptions}
              value={field.value}
              placeholder="Choose city"
              disabled={!state}
              onChange={field.onChange}
            />
          )}
        />
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
