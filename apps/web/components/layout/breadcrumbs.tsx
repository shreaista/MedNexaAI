import Link from "next/link";

export type Crumb = { label: string; href?: string };

export function AppBreadcrumbs({ items }: { items: Crumb[] }) {
  if (items.length === 0) return null;
  return (
    <nav className="mb-4 text-xs text-zinc-500" aria-label="Breadcrumb">
      <ol className="flex flex-wrap items-center gap-x-1.5 gap-y-1">
        {items.map((item, i) => (
          <li key={`${item.label}-${i}`} className="flex items-center gap-1.5">
            {i > 0 ? <span className="text-zinc-300">/</span> : null}
            {item.href ? (
              <Link href={item.href} className="font-medium hover:text-emerald-800">
                {item.label}
              </Link>
            ) : (
              <span className="font-medium text-zinc-700">{item.label}</span>
            )}
          </li>
        ))}
      </ol>
    </nav>
  );
}
