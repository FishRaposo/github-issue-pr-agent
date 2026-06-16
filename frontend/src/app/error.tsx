"use client";

import { useEffect } from "react";
import { AlertTriangle } from "lucide-react";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // eslint-disable-next-line no-console
    console.error(error);
  }, [error]);

  return (
    <div className="flex flex-col items-center justify-center rounded-xl border border-rose-200 bg-rose-50 p-12 text-center">
      <AlertTriangle className="mb-4 h-10 w-10 text-rose-400" />
      <h2 className="mb-2 text-lg font-semibold text-rose-800">
        Something went wrong
      </h2>
      <p className="mb-4 max-w-md text-sm text-rose-600">
        {error.message || "An unexpected error occurred."}
      </p>
      <button
        onClick={reset}
        className="rounded-lg bg-rose-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-rose-700"
      >
        Try again
      </button>
    </div>
  );
}
