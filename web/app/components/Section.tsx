export function Section({
  tag,
  title,
  meta,
  id,
  first,
  live,
  children,
}: {
  tag: string;
  title: React.ReactNode;
  meta?: string;
  id?: string;
  first?: boolean;
  live?: boolean;
  children: React.ReactNode;
}) {
  return (
    <section
      id={id}
      className={`section ${first ? "section-first" : ""} ${live ? "section-live" : ""}`}
      style={{ scrollMarginTop: 80 }}
    >
      <header className="section-header">
        <div className="section-tag">
          {tag}
          {live && (
            <span className="section-live-badge" aria-label="Live section">
              <span className="section-live-dot" />
              LIVE
            </span>
          )}
        </div>
        <h2 className="section-title">{title}</h2>
        {meta && <div className="section-meta">{meta}</div>}
      </header>
      {children}
    </section>
  );
}
