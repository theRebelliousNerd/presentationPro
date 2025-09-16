import Link from "next/link";

const devPages = [
  {
    href: "/dev/visioncv",
    title: "VisionCV Tools",
    description: "Run computer-vision agent endpoints with drag-and-drop screenshots.",
  },
  {
    href: "/dev/search-cache",
    title: "Search Cache Viewer",
    description: "Inspect cached research lookups captured during agent runs.",
  },
];

export default function DevHome() {
  return (
    <div className="mx-auto flex w-full max-w-4xl flex-col gap-6 p-8">
      <div>
        <h1 className="text-3xl font-bold">Developer UI</h1>
        <p className="text-muted-foreground">
          Quick links to internal tooling and diagnostics used while building PresentationPro.
        </p>
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        {devPages.map((page) => (
          <Link
            key={page.href}
            href={page.href}
            className="rounded-lg border border-border bg-card p-4 transition hover:border-primary hover:bg-muted"
          >
            <h2 className="text-lg font-semibold">{page.title}</h2>
            <p className="mt-2 text-sm text-muted-foreground">{page.description}</p>
            <span className="mt-4 inline-flex items-center text-sm font-medium text-primary">
              Open {'>'}
            </span>
          </Link>
        ))}
      </div>
    </div>
  );
}
