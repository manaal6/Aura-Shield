import { useRef, useState, type KeyboardEvent, type ReactNode } from 'react';
import { AnimatePresence, motion, useReducedMotion } from 'framer-motion';
import { useSearchParams } from 'react-router-dom';

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
  const [searchParams, setSearchParams] = useSearchParams();
  const requested = searchParams.get('tab');
  const [active, setActiveState] = useState(
    requested && tabs.some((t) => t.id === requested) ? requested : (initial ?? tabs[0].id),
  );
  const reduce = useReducedMotion();
  const listRef = useRef<HTMLDivElement>(null);
  const current = tabs.find((t) => t.id === active) ?? tabs[0];

  function setActive(id: string) {
    setActiveState(id);
    const next = new URLSearchParams(searchParams);
    next.set('tab', id);
    setSearchParams(next, { replace: true });
  }

  function onKeyDown(e: KeyboardEvent<HTMLDivElement>) {
    const i = tabs.findIndex((t) => t.id === active);
    let next = i;
    if (e.key === 'ArrowRight') next = (i + 1) % tabs.length;
    else if (e.key === 'ArrowLeft') next = (i - 1 + tabs.length) % tabs.length;
    else if (e.key === 'Home') next = 0;
    else if (e.key === 'End') next = tabs.length - 1;
    else return;
    e.preventDefault();
    setActive(tabs[next].id);
    const buttons = listRef.current?.querySelectorAll<HTMLButtonElement>('[role="tab"]');
    buttons?.[next]?.focus();
  }

  return (
    <div>
      <header className="section-head">
        <h1 className="section-title">{title}</h1>
        <p className="section-intro">{intro}</p>
      </header>

      <div className="tabs" role="tablist" aria-label={`${title} sections`} ref={listRef} onKeyDown={onKeyDown}>
        {tabs.map((t) => (
          <button
            key={t.id}
            type="button"
            role="tab"
            id={`tab-${t.id}`}
            aria-selected={t.id === active}
            aria-controls={`panel-${t.id}`}
            tabIndex={t.id === active ? 0 : -1}
            className="tab"
            onClick={() => setActive(t.id)}
          >
            {t.id === active && (
              <motion.span
                layoutId="tab-indicator"
                className="tab-indicator"
                transition={reduce ? { duration: 0 } : { type: 'spring', stiffness: 520, damping: 40 }}
              />
            )}
            <span className="tab-label">{t.label}</span>
          </button>
        ))}
      </div>

      <div
        role="tabpanel"
        id={`panel-${current.id}`}
        aria-labelledby={`tab-${current.id}`}
        className="tabpanel"
        tabIndex={0}
      >
        <AnimatePresence mode="wait" initial={false}>
          <motion.div
            key={current.id}
            initial={reduce ? false : { opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={reduce ? undefined : { opacity: 0, y: -3 }}
            transition={{ duration: 0.18, ease: [0.2, 0.7, 0.3, 1] }}
          >
            {current.render()}
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
}
