import AnalyzePage from '../pages/AnalyzePage';
import PipelinePage from '../pages/PipelinePage';
import ToolSecurityPage from '../pages/ToolSecurityPage';
import BenchmarkPage from '../pages/BenchmarkPage';
import FusionLabPage from '../pages/FusionLabPage';
import RedTeamPage from '../pages/RedTeamPage';
import ReliabilityPage from '../pages/ReliabilityPage';
import ConstitutionPage from '../pages/ConstitutionPage';
import AdaptivePage from '../pages/AdaptivePage';
import EvidencePage from '../pages/EvidencePage';
import LogsPage from '../pages/LogsPage';
import ReproducibilityPage from '../pages/ReproducibilityPage';
import AlignmentPage, { DpoPanel, UnlearningPanel } from '../pages/AlignmentPage';
import { useEvidence } from '../api/evidence';
import { SectionShell } from '../components/SectionShell';

export function SystemSection() {
  return (
    <SectionShell
      title="System" intro="What AURA Shield is and how a request flows through it."
      tabs={[
        { id: 'analyze', label: 'Analyze', render: () => <AnalyzePage /> },
        { id: 'pipeline', label: 'Pipeline', render: () => <PipelinePage /> },
        { id: 'tools', label: 'Tools', render: () => <ToolSecurityPage /> },
      ]}
    />
  );
}

export function EvaluationSection() {
  return (
    <SectionShell
      title="Evaluation" intro="Frozen benchmark, fusion analysis, red-team, and reliability — DEV vs held-out strictly separated."
      tabs={[
        { id: 'benchmark', label: 'Benchmark', render: () => <BenchmarkPage /> },
        { id: 'fusion', label: 'Fusion', render: () => <FusionLabPage /> },
        { id: 'redteam', label: 'Red Team', render: () => <RedTeamPage /> },
        { id: 'reliability', label: 'Reliability', render: () => <ReliabilityPage /> },
      ]}
    />
  );
}

export function SecuritySection() {
  return (
    <SectionShell
      title="Security" intro="Policy enforcement, adaptive defense, and raw evidence artifacts."
      tabs={[
        { id: 'constitution', label: 'Constitution', render: () => <ConstitutionPage /> },
        { id: 'adaptive', label: 'Adaptive Defense', render: () => <AdaptivePage /> },
        { id: 'evidence', label: 'Evidence', render: () => <EvidencePage /> },
      ]}
    />
  );
}

function DpoTab() {
  const { data, error } = useEvidence();
  if (error) return <div className="panel"><p className="error">Failed to load: {error}</p></div>;
  if (!data) return <div className="panel"><p className="muted">Loading…</p></div>;
  return <DpoPanel data={data} />;
}

function UnlearningTab() {
  const { data, error } = useEvidence();
  if (error) return <div className="panel"><p className="error">Failed to load: {error}</p></div>;
  if (!data) return <div className="panel"><p className="muted">Loading…</p></div>;
  return <UnlearningPanel data={data} />;
}

export function AlignmentSection() {
  return (
    <SectionShell
      title="Alignment" intro="Model-level preference training and targeted behavior removal — both with kept negative results."
      tabs={[
        { id: 'dpo', label: 'DPO', render: () => <DpoTab /> },
        { id: 'unlearning', label: 'Unlearning', render: () => <UnlearningTab /> },
      ]}
    />
  );
}

// Re-exported for any direct deep-link use; the section composes both panels.
export { AlignmentPage };

export function ReproducibilitySection() {
  return (
    <SectionShell
      title="Reproducibility" intro="Datasets, hashes, commands, artifacts, and audit logs."
      tabs={[
        { id: 'experiments', label: 'Experiments', render: () => <ReproducibilityPage /> },
        { id: 'logs', label: 'Logs', render: () => <LogsPage /> },
      ]}
    />
  );
}
