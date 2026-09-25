import { useEffect, useState } from 'react';

export interface EvidenceBlock {
  has_data: boolean;
  data?: unknown;
}

export type EvidenceData = Record<string, EvidenceBlock>;

export function useEvidence() {
  const [data, setData] = useState<EvidenceData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch('/api/evidence')
      .then((r) => {
        if (!r.ok) throw new Error(`Request failed (${r.status})`);
        return r.json();
      })
      .then(setData)
      .catch((e: Error) => setError(e.message));
  }, []);

  return { data, error };
}

export function Missing({ label }: { label: string }) {
  return (
    <div className="panel">
      <h3>{label}</h3>
      <p className="muted">NOT AVAILABLE — experiment artifact absent (not run). No number invented.</p>
    </div>
  );
}

export function Cards({ items }: { items: { k: string; v: string }[] }) {
  return (
    <div className="cards">
      {items.map((c) => (
        <div className="card" key={c.k}>
          <div className="k">{c.k}</div>
          <div className="v">{c.v}</div>
        </div>
      ))}
    </div>
  );
}
