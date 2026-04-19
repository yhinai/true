export function Section({
  tag,
  title,
  meta,
  id,
  first,
  children,
}: {
  tag: string;
  title: React.ReactNode;
  meta?: string;
  id?: string;
  first?: boolean;
  children: React.ReactNode;
}) {
  return (
    <section
      id={id}
      className={`section ${first ? "section-first" : ""}`}
      style={{ scrollMarginTop: 80 }}
    >
      <header className="section-header">
        <div className="section-tag">{tag}</div>
        <h2 className="section-title">{title}</h2>
        {meta && <div className="section-meta">{meta}</div>}
      </header>
      {children}
    </section>
  );
}
