import { z } from "zod";

export const searchFormSchema = z.object({
  industry: z
    .string()
    .trim()
    .min(2, "Industry must be at least 2 characters.")
    .max(100),
  country: z
    .string()
    .trim()
    .min(2, "Country must be at least 2 characters.")
    .max(100),
  state: z.string().trim().min(1, "State is required.").max(100),
  city: z.string().trim().min(1, "City is required.").max(100),
  perPage: z.coerce.number().int().min(1).max(100)
});

export type SearchFormValues = z.infer<typeof searchFormSchema>;
