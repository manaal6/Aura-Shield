async function handle<T>(res: Response | Promise<Response>): Promise<T> {
  const r = await res;
  const data = await r.json().catch(() => ({}));
  if (!r.ok) {
    throw new Error((data as { error?: string; detail?: string }).error
      ?? (data as { detail?: string }).detail
      ?? `Request failed (${r.status})`);
  }
  return data as T;
}

export interface AnalyzeResult {
  request_id: string;
  decision: string;
  risk_score: number;
  explanation: string;
  signals: {
    rule: { signal: number; matched: boolean; patterns: string[] };
    llm: { signal: number; is_suspicious: boolean; reasoning: string; used_fallback: boolean };
    constitution: {
      signal: number; version: number; used_fallback: boolean; reasoning: string;
      violations: { principle_id: string; confidence: number; explanation: string }[];
    };
  };
  llm_response: string | null;
}

export interface LogRow {
  request_id: string;
  timestamp: string;
  user_prompt: string;
  decision: string;
  risk_score: number | null;
  rule_signal: number | null;
  llm_signal: number | null;
  constitution_signal: number | null;
  llm_used_fallback: boolean;
  constitution_fallback: boolean | null;
  explanation: string;
  human_flagged: boolean;
}

export interface Principle {
  id: string;
  version_added: number;
  principle_text: string;
  rationale: string;
  status: string;
}

export interface PendingPrinciple {
  id: number;
  principle_id?: string | null;
  principle_text: string;
  rationale: string;
  status: string;
  triggered_by: unknown;
  drafted_reasoning?: string | null;
  drafted_at?: string | null;
  [k: string]: unknown;
}

export interface ChangelogEntry {
  timestamp: string;
  action: string;
  principle_id?: string;
  actor?: string;
  reason?: string;
  [k: string]: unknown;
}

export interface ConstitutionData {
  version: number;
  principles: Principle[];
  pending: PendingPrinciple[];
  changelog: ChangelogEntry[];
}

export interface BenchmarkData {
  has_data: boolean;
  real_llm_calls_used?: boolean;
  metrics?: Record<string, number>;
  by_category?: Record<string, { total: number; flagged: number }>;
  attribution?: {
    total_flagged: number;
    rule_and_llm: number;
    rule_only_support: number;
    llm_only: number;
    constitution_only: number | null;
  };
  n?: number;
}

export function analyze(data: { user_prompt: string; source_content?: string | null }) {
  return handle<AnalyzeResult>(fetch('/api/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  }));
}

export function fetchLogs(params: Record<string, string | number> = {}) {
  const query = new URLSearchParams(
    Object.entries(params).map(([k, v]) => [k, String(v)]),
  ).toString();
  return handle<{ rows: LogRow[] }>(fetch(`/api/logs?${query}`));
}

export function flagLog(requestId: string) {
  return handle<{ ok: boolean }>(fetch(`/api/logs/${encodeURIComponent(requestId)}/flag`, { method: 'POST' }));
}

export function fetchConstitution() {
  return handle<ConstitutionData>(fetch('/api/constitution'));
}

export function reviewPrinciple(pendingId: number, action: 'approve' | 'reject', actor: string, reason?: string) {
  return handle<{ ok: boolean; new_version?: number }>(
    fetch(`/api/constitution/pending/${pendingId}/${action}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ actor, reason }),
    }),
  );
}

export function fetchBenchmark() {
  return handle<BenchmarkData>(fetch('/api/benchmark'));
}

export interface HeldoutBaselineRow {
  key: string;
  config: string;
  name: string;
  n_total: number;
  n_attacks: number;
  n_benign: number;
  recall: number | null;
  precision: number | null;
  f1: number | null;
  fpr: number | null;
  true_positives: number | null;
  false_negatives: number | null;
  false_positives: number | null;
  recall_ci_95: [number, number] | null;
  avg_latency_ms: number | null;
  fallback_rows: number;
  run_dir: string;
}

export interface MeasuredData {
  heldout_baselines: { description: string; rows: HeldoutBaselineRow[] } | null;
  adaptive_before_after: {
    description: string;
    before: { constitution_version: number; recall: number; precision: number; f1: number; fpr: number; true_positives: number; false_positives: number; run_dir: string };
    after: { constitution_version: number; recall: number; precision: number; f1: number; fpr: number; true_positives: number; false_positives: number; run_dir: string };
  } | null;
  soc: {
    total_prompts_evaluated: number;
    legitimate_soc_queries: number;
    benign_utility_rate: number;
    embedded_attacks_evaluated: number;
    embedded_payload_detection_rate: number;
    tool_injections_evaluated: number;
    tool_authorization_enforcement_rate: number;
  } | null;
}

export function fetchMeasured() {
  return handle<MeasuredData>(fetch('/api/measured'));
}
