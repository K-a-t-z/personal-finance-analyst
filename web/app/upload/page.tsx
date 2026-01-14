"use client";

import { useState } from "react";
import Link from "next/link";
import { ingestCsv } from "@/src/lib/api";

type UploadState = "idle" | "loading" | "success" | "error";

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [state, setState] = useState<UploadState>("idle");
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      setState("idle");
      setResult(null);
      setError(null);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError("Please select a file first");
      return;
    }

    setState("loading");
    setError(null);
    setResult(null);

    try {
      const response = await ingestCsv(file);
      setResult(response);
      setState("success");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to upload file");
      setState("error");
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-50 font-sans dark:bg-black py-12 px-4">
      <div className="w-full max-w-2xl">
        <div className="bg-white dark:bg-zinc-900 rounded-lg shadow-lg p-8 border border-gray-200 dark:border-gray-800">
          <h1 className="text-3xl font-bold mb-6 text-black dark:text-zinc-50">
            Upload CSV File
          </h1>

          <div className="space-y-6">
            {/* File Input */}
            <div>
              <label
                htmlFor="csv-file"
                className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
              >
                Select CSV File
              </label>
              <input
                id="csv-file"
                type="file"
                accept=".csv"
                onChange={handleFileChange}
                className="block w-full text-sm text-gray-500 dark:text-gray-400
                  file:mr-4 file:py-2 file:px-4
                  file:rounded-full file:border-0
                  file:text-sm file:font-semibold
                  file:bg-blue-50 file:text-blue-700
                  hover:file:bg-blue-100
                  dark:file:bg-blue-900 dark:file:text-blue-300
                  dark:hover:file:bg-blue-800
                  cursor-pointer"
                disabled={state === "loading"}
              />
              {file && (
                <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
                  Selected: {file.name} ({(file.size / 1024).toFixed(2)} KB)
                </p>
              )}
            </div>

            {/* Upload Button */}
            <button
              onClick={handleUpload}
              disabled={!file || state === "loading"}
              className="w-full px-6 py-3 bg-blue-600 text-white font-medium rounded-lg
                hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed
                transition-colors"
            >
              {state === "loading" ? "Uploading..." : "Upload"}
            </button>

            {/* Loading State */}
            {state === "loading" && (
              <div className="flex items-center justify-center py-4">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              </div>
            )}

            {/* Error State */}
            {state === "error" && error && (
              <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                <h3 className="text-sm font-semibold text-red-800 dark:text-red-400 mb-2">
                  Upload Failed
                </h3>
                <p className="text-sm text-red-700 dark:text-red-300">{error}</p>
              </div>
            )}

            {/* Success State */}
            {state === "success" && result && (
              <div className="space-y-4">
                <div className="p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
                  <h3 className="text-sm font-semibold text-green-800 dark:text-green-400 mb-2">
                    Upload Successful!
                  </h3>
                  <p className="text-sm text-green-700 dark:text-green-300">
                    Your CSV file has been processed successfully.
                  </p>
                </div>

                <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
                  <h4 className="text-sm font-semibold text-gray-800 dark:text-gray-200 mb-3">
                    Upload Details
                  </h4>
                  <pre className="text-xs text-gray-700 dark:text-gray-300 overflow-auto">
                    {JSON.stringify(result, null, 2)}
                  </pre>
                </div>

                <Link
                  href="/chat"
                  className="block w-full px-6 py-3 bg-green-600 text-white font-medium rounded-lg
                    hover:bg-green-700 text-center transition-colors"
                >
                  Go to Chat
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
