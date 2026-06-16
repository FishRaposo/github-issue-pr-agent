import { AlertCircle, RefreshCw } from "lucide-react";

interface Props {
  title?: string;
  message: string;
  onRetry?: () => void;
}

/** A standard error panel for failed data views (real HTTP 4xx/5xx). */
export default function ErrorState({ title = "Couldn't load data", message, onRetry }: Props) {
  return (
    <div
      className="flex flex-col items-center justify-center rounded-xl border border-rose-200 bg-rose-50 p-10 text-center"
      role="alert"
    >
      <AlertCircle className="mb-3 h-9 w-9 text-rose-400" />
      <h3 className="mb-1 text-base font-semibold text-rose-800">{title}</h3>
      <p className="mb-4 max-w-md text-sm text-rose-600">{message}</p>
      {onRetry && (
        <button onClick={onRetry} className="btn-secondary border-rose-300 text-rose-700">
          <RefreshCw className="h-4 w-4" />
          Retry
        </button>
      )}
    </div>
  );
}
