export default function StatTile({ icon: Icon, label, value, detail, tone = "light" }) {
  return (
    <div className={`stat-tile stat-tile-${tone}`}>
      {Icon && <Icon size={28} strokeWidth={2.8} aria-hidden="true" />}
      <strong>{value}</strong>
      <span>{label}</span>
      {detail && <small>{detail}</small>}
    </div>
  );
}
