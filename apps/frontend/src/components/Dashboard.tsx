import { useState } from "react";
import { Link } from "react-router-dom";

export function ProgressRing({ value, size = 92 }: { value: number; size?: number }) {
  const clamped = Math.max(0, Math.min(100, Math.round(value)));
  const radius = 40;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (clamped / 100) * circumference;

  return (
    <div className="ring" style={{ width: size, height: size }} role="img" aria-label={`${clamped} percent`}>
      <svg viewBox="0 0 100 100" aria-hidden="true">
        <circle className="ring-track" cx="50" cy="50" r={radius} />
        <circle
          className="ring-value"
          cx="50"
          cy="50"
          r={radius}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
        />
      </svg>
      <strong>{clamped}%</strong>
    </div>
  );
}

function previewNote(note: string, max = 150): { text: string; truncated: boolean } {
  const cleaned = note.replace(/\s+/g, " ").trim();
  if (cleaned.length <= max) return { text: cleaned, truncated: false };

  const slice = cleaned.slice(0, max);
  const sentence = slice.lastIndexOf(". ");
  const space = slice.lastIndexOf(" ");
  const breakAt = sentence > 70 ? sentence + 1 : space > 70 ? space : max;
  return { text: `${cleaned.slice(0, breakAt).trimEnd()}…`, truncated: true };
}

export function DashboardPanel({
  eyebrow,
  title,
  note,
  progress,
  progressLabel,
  stats,
}: {
  eyebrow: string;
  title?: string;
  note?: string | null;
  progress: number;
  progressLabel: string;
  stats: { label: string; value: number | string; to?: string }[];
}) {
  const [expanded, setExpanded] = useState(false);
  const raw = note?.trim() ?? "";
  const preview = raw ? previewNote(raw) : null;

  return (
    <section className="dash">
      <div className="dash-main">
        <div className="dash-copy">
          <p className="eyebrow">{eyebrow}</p>
          {title && <h1>{title}</h1>}
          {preview && (
            <div className="dash-note-block">
              <p className={`dash-note${expanded ? " is-expanded" : ""}`}>
                {expanded ? raw : preview.text}
              </p>
              {preview.truncated && (
                <button
                  type="button"
                  className="dash-more"
                  onClick={() => setExpanded((open) => !open)}
                >
                  {expanded ? "Show less" : "Show more"}
                </button>
              )}
            </div>
          )}
        </div>
        <div className="ring-wrap">
          <ProgressRing value={progress} />
          <span>{progressLabel}</span>
        </div>
      </div>
      <div className="dash-stats">
        {stats.map((stat) =>
          stat.to ? (
            <Link key={stat.label} className="dash-stat" to={stat.to}>
              <span>{stat.label}</span>
              <strong>{stat.value}</strong>
            </Link>
          ) : (
            <div key={stat.label} className="dash-stat">
              <span>{stat.label}</span>
              <strong>{stat.value}</strong>
            </div>
          ),
        )}
      </div>
    </section>
  );
}
