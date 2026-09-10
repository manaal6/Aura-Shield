export async function analyze(data: { user_prompt: string; source_content?: string }) {
  const response = await fetch('/api/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return response.json();
}

export async function fetchLogs(params: Record<string, string | number> = {}) {
  const query = new URLSearchParams(params as any).toString();
  const res = await fetch(`/api/logs?${query}`);
  return res.json();
}

export async function fetchConstitution() {
  const res = await fetch('/api/constitution');
  return res.json();
}

export async function fetchBenchmark() {
  const res = await fetch('/api/benchmark');
  return res.json();
}
