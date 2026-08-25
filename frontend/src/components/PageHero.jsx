export default function PageHero({ eyebrow, title, children, action }) {
  return (
    <div className="page-hero">
      <div>
        {eyebrow && <p className="eyebrow">{eyebrow}</p>}
        <h1>{title}</h1>
        {children && <div className="hero-copy">{children}</div>}
      </div>
      {action && <div className="hero-action">{action}</div>}
    </div>
  );
}
