import type { Metadata } from "next";
import "@/styles/globals.css";
import { AppProviders } from "@/app/providers";

export const metadata: Metadata = {
  title: "Lead Generator App",
  description: "Production search dashboard for lead generation"
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body>
        <AppProviders>{children}</AppProviders>
      </body>
    </html>
  );
}
