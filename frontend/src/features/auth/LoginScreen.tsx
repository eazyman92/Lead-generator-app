"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { LockKeyhole, Mail, Sparkles, UserPlus } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Spinner } from "@/components/ui/spinner";
import { login, register, userFriendlyError } from "@/services/api-client";
import { cn } from "@/utils/cn";

const loginSchema = z.object({
  email: z.string().email("Enter a valid email address."),
  password: z
    .string()
    .min(12, "Password must be at least 12 characters.")
    .regex(/[A-Z]/, "Password must include an uppercase letter.")
    .regex(/[a-z]/, "Password must include a lowercase letter.")
    .regex(/[0-9]/, "Password must include a number.")
});

type LoginFormValues = z.infer<typeof loginSchema>;

export function LoginScreen() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [mode, setMode] = useState<"login" | "register">("login");
  const form = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: "",
      password: ""
    }
  });

  const mutation = useMutation({
    mutationFn: (values: LoginFormValues) =>
      mode === "login"
        ? login(values.email, values.password)
        : register(values.email, values.password),
    onSuccess: async (user) => {
      queryClient.setQueryData(["auth", "me"], user);
      toast.success(
        mode === "login" ? "Signed in successfully." : "Account created."
      );
      router.replace("/");
    },
    onError: (error) => toast.error(userFriendlyError(error))
  });

  return (
    <main className="flex min-h-screen items-center justify-center px-4 py-10">
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35 }}
        className="w-full max-w-md"
      >
        <div className="mb-6 flex items-center gap-3">
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
            <h1 className="text-xl font-semibold">
              {mode === "login" ? "Sign in" : "Create account"}
            </h1>
          </div>
        </div>

        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold">
              {mode === "login" ? "Search workspace access" : "Start searching"}
            </h2>
            <p className="mt-1 text-sm text-mutedForeground">
              {mode === "login"
                ? "Use your account to launch business searches and review collected leads."
                : "Create your first workspace account with the existing secure registration flow."}
            </p>
          </CardHeader>
          <CardContent>
            <form
              className="space-y-4"
              onSubmit={form.handleSubmit((values) => mutation.mutate(values))}
            >
              <label className="block space-y-2">
                <span className="text-sm text-mutedForeground">Email</span>
                <div className="relative">
                  <Mail className="absolute left-3 top-3 h-4 w-4 text-muted" />
                  <Input
                    className="pl-9"
                    type="email"
                    autoComplete="email"
                    {...form.register("email")}
                  />
                </div>
                {form.formState.errors.email ? (
                  <span className="text-xs text-destructive">
                    {form.formState.errors.email.message}
                  </span>
                ) : null}
              </label>

              <label className="block space-y-2">
                <span className="text-sm text-mutedForeground">Password</span>
                <div className="relative">
                  <LockKeyhole className="absolute left-3 top-3 h-4 w-4 text-muted" />
                  <Input
                    className="pl-9"
                    type="password"
                    autoComplete="current-password"
                    {...form.register("password")}
                  />
                </div>
                {form.formState.errors.password ? (
                  <span className="text-xs text-destructive">
                    {form.formState.errors.password.message}
                  </span>
                ) : null}
              </label>

              <Button
                className="w-full"
                type="submit"
                disabled={mutation.isPending}
              >
                {mutation.isPending ? <Spinner /> : null}
                {mode === "login" ? "Sign in" : "Create account"}
              </Button>
            </form>

            <div className="mt-4 border-t border-border pt-4">
              <Button
                className="w-full"
                type="button"
                variant="ghost"
                onClick={() => {
                  setMode((current) =>
                    current === "login" ? "register" : "login"
                  );
                  form.clearErrors();
                }}
              >
                {mode === "login" ? <UserPlus className="h-4 w-4" /> : null}
                {mode === "login"
                  ? "Create a new account"
                  : "Use an existing account"}
              </Button>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </main>
  );
}
