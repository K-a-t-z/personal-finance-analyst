"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { healthCheck } from "@/src/lib/api";

export default function Home() {
  const [backendStatus, setBackendStatus] = useState<"Online" | "Offline" | "Checking">("Checking");

  useEffect(() => {
    const checkHealth = async () => {
      try {
        await healthCheck();
        setBackendStatus("Online");
      } catch (error) {
        setBackendStatus("Offline");
      }
    };

    checkHealth();
    // Check health every 30 seconds
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-50 font-sans dark:bg-black">
      <main className="flex min-h-screen w-full max-w-3xl flex-col items-center justify-center gap-8 py-16 px-8">
        <div className="flex flex-col items-center gap-6 text-center">
          <h1 className="text-4xl font-bold leading-tight tracking-tight text-black dark:text-zinc-50">
            Personal Finance Analyst
          </h1>
          <p className="max-w-md text-lg leading-8 text-zinc-600 dark:text-zinc-400">
            Track and analyze your spending with intelligent insights. Upload your transaction data
            and ask questions about your finances.
          </p>
        </div>

        <div className="flex flex-col gap-4 text-base font-medium sm:flex-row">
          <Link
            href="/upload"
            className="flex h-12 w-full items-center justify-center rounded-full bg-foreground px-8 text-background transition-colors hover:bg-[#383838] dark:hover:bg-[#ccc] sm:w-auto"
          >
            Upload CSV
          </Link>
          <Link
            href="/chat"
            className="flex h-12 w-full items-center justify-center rounded-full border border-solid border-black/[.08] px-8 transition-colors hover:border-transparent hover:bg-black/[.04] dark:border-white/[.145] dark:hover:bg-[#1a1a1a] sm:w-auto"
          >
            Chat
          </Link>
        </div>

        <div className="mt-8 flex items-center gap-2 text-sm text-zinc-600 dark:text-zinc-400">
          <span className="font-medium">Backend status:</span>
          <span
            className={`font-semibold ${
              backendStatus === "Online"
                ? "text-green-600 dark:text-green-400"
                : backendStatus === "Offline"
                  ? "text-red-600 dark:text-red-400"
                  : "text-yellow-600 dark:text-yellow-400"
            }`}
          >
            {backendStatus}
          </span>
        </div>
      </main>
    </div>
  );
}
