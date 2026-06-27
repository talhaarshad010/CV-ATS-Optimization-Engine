import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Navbar from "@/components/Navbar";
import { AppProvider } from "@/lib/store";

const inter = Inter({ subsets: ["latin"], variable: "--font-sans" });

export const metadata: Metadata = {
  title: "CV Platform",
  description: "CV Extraction and ATS Scoring Platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={inter.variable}>
      <body className={`${inter.className} min-h-screen flex flex-col`} style={{ background: 'var(--page-bg-gradient)', backgroundAttachment: 'fixed', color: 'var(--text-primary)' }}>
        <AppProvider>
          <Navbar />
          <div className="flex-1 w-full">
            {children}
          </div>
        </AppProvider>
      </body>
    </html>
  );
}
