export default function AppLoading() {
  return (
    <div className="mx-auto max-w-6xl animate-pulse space-y-8">
      <div className="h-8 w-48 rounded-md bg-zinc-200" />
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-28 rounded-xl border border-zinc-100 bg-white p-4 shadow-sm">
            <div className="h-3 w-24 rounded bg-zinc-200" />
            <div className="mt-4 h-8 w-16 rounded bg-zinc-200" />
          </div>
        ))}
      </div>
      <div className="h-64 rounded-xl border border-zinc-100 bg-white shadow-sm" />
    </div>
  );
}
