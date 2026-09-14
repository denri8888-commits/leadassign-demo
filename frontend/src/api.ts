export type Dashboard = {
  kpi: {
    total_applications: number
    recommended: number
    queued: number
    expected_gm: number
    avg_gm_per_talk: number
    lift_vs_manual_pct: number
    lift_vs_manual_abs: number
    manual_gm: number
    random_gm: number
    greedy_gm: number
    optimal_gm: number
  }
  charts: any
  manager_load: Record<string, number>
  disclaimer: string
  core_idea: string
  scenario: string
  scenario_label: string
  seed: number
  as_of: string
  mode: string
  timestamp: string
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, init)
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    const msg = data?.detail?.error || data?.error || res.statusText
    throw new Error(typeof msg === 'string' ? msg : JSON.stringify(msg))
  }
  return data as T
}

export const api = {
  dashboard: () => request<Dashboard>('/api/dashboard'),
  applications: (params: Record<string, string | boolean | undefined> = {}) => {
    const q = new URLSearchParams()
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== '') q.set(k, String(v))
    })
    return request<{ items: any[]; total: number }>(`/api/applications?${q}`)
  },
  application: (id: string) => request<any>(`/api/applications/${id}`),
  managers: () => request<{ items: any[] }>('/api/managers'),
  matrix: () => request<{ items: any[] }>('/api/matrix'),
  capacity: () => request<any>('/api/capacity'),
  simulation: (days: number, auto_share: number) =>
    request<any>(`/api/simulation?days=${days}&auto_share=${auto_share}`),
  settings: () => request<{ settings: any; helpers: Record<string, string>; scenarios: Record<string, string> }>('/api/settings'),
  updateSettings: (body: any) =>
    request('/api/settings', { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }),
  recalculate: () => request('/api/recalculate', { method: 'POST' }),
  generate: (seed: number, scenario: string) =>
    request('/api/demo/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ seed, scenario }),
    }),
  override: (id: string, body: { manager: string; reason: string; comment?: string }) =>
    request(`/api/recommendations/${id}/override`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }),
  result: () => request<any>('/api/result'),
  assumptions: () => request<{ items: { title: string; text: string }[] }>('/api/assumptions'),
  roadmap: () => request<any>('/api/roadmap'),
  regions: () => request<{ items: string[] }>('/api/regions'),
  products: () => request<{ items: string[] }>('/api/products'),
  importPreview: async (file: File, kind: string) => {
    const fd = new FormData()
    fd.append('file', file)
    return request<any>(`/api/import/preview?kind=${kind}`, { method: 'POST', body: fd })
  },
  importApply: async (file: File, kind: string, mapping: Record<string, string>) => {
    const fd = new FormData()
    fd.append('file', file)
    const q = new URLSearchParams({ kind, mapping_json: JSON.stringify(mapping) })
    return request<any>(`/api/import/apply?${q}`, { method: 'POST', body: fd })
  },
}

export function money(v: number) {
  return `${new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 0 }).format(v)} BYN`
}

export function pct(v: number, digits = 1) {
  return `${(v * (v <= 1 ? 100 : 1)).toFixed(digits)}%`.replace('.', ',')
}

export function pctAlready(v: number, digits = 1) {
  return `${v.toFixed(digits)}%`.replace('.', ',')
}
