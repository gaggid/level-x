import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Toaster } from "@/components/ui/sonner";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "LevelX - X Growth Intelligence",
  description: "AI-powered X growth intelligence that compares you with similar accounts and tells you exactly what to copy.",
  keywords: ["Twitter growth", "X analytics", "social media growth", "content strategy"],
  authors: [{ name: "LevelX" }],
  openGraph: {
    title: "LevelX - X Growth Intelligence",
    description: "See exactly why accounts at your level are growing faster",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        {children}
        <Toaster />
      </body>
    </html>
  );
}