import { useState, type ReactNode } from 'react';

export interface SubTab {
  id: string;
  label: string;
  render: () => ReactNode;
}

export function SectionShell({ title, intro, tabs, initial }: {
  title: string;
  intro: string;
  tabs: SubTab[];
  initial?: string;
}) {
  const [active, setActive] = useState(initial ?? tabs[0].id);
  const current = tabs.find((t) => t.id === active) ?? tabs[0];
  return (
    <div>
      <h2>{title}</h2>
      <p className="muted">{intro}</p>
      <div className="subnav" role="tablist" aria-label={`${title} sections`}>
        {tabs.map((t) => (
          <button
            key={t.id}
            role="tab"
            aria-selected={t.id === active}
            className={t.id === active ? 'subnav-link active' : 'subnav-link'}
            onClick={() => setActive(t.id)}
          >
            {t.label}
          </button>
        ))}
      </div>
      <div style={{ marginTop: '1rem' }}>{current.render()}</div>
    </div>
  );
}
