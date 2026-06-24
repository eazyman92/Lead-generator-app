export default function HomePage() {
  return (
    <main className="min-h-screen bg-background text-foreground">
      <section className="mx-auto flex min-h-screen max-w-5xl flex-col justify-center px-6">
        <p className="text-sm font-medium text-primary">Lead Generator App</p>
        <h1 className="mt-3 text-4xl font-semibold">Foundation ready</h1>
        <p className="mt-4 max-w-2xl text-base text-muted">
          Phase 0 scaffold for the frontend, backend, worker, database, and Docker services.
        </p>
      </section>
    </main>
  );
}

