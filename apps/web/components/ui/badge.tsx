import { cn } from "@/lib/utils";

export function Badge({
  className,
  variant = "neutral",
  ...props
}: React.HTMLAttributes<HTMLSpanElement> & {
  variant?: "neutral" | "success" | "warning" | "danger" | "info" | "muted";
}) {
  const variants = {
    neutral: "bg-zinc-100 text-zinc-700",
    success: "bg-emerald-50 text-emerald-800 ring-1 ring-emerald-100",
    warning: "bg-amber-50 text-amber-900 ring-1 ring-amber-100",
    danger: "bg-rose-50 text-rose-800 ring-1 ring-rose-100",
    info: "bg-blue-50 text-blue-900 ring-1 ring-blue-100",
    muted: "bg-slate-100 text-slate-700 ring-1 ring-slate-200",
  };
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium",
        variants[variant],
        className,
      )}
      {...props}
    />
  );
}
