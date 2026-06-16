import Link from "next/link";
import { Compass } from "lucide-react";

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-ink-300 bg-ink-50/50 p-16 text-center">
      <Compass className="mb-4 h-10 w-10 text-ink-400" />
      <h1 className="text-xl font-bold text-ink-900">Page not found</h1>
      <p className="mt-1 text-sm text-ink-500">
        The page you’re looking for doesn’t exist.
      </p>
      <Link href="/" className="btn-primary mt-5">
        Back to overview
      </Link>
    </div>
  );
}
