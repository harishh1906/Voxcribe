// ── API Client ──

export interface Transcription {
  id: string
  title: string
  transcription_text: string
  language_detected: string | null
  duration_seconds: number
  word_count: number
  status: string
  audio_file_path: string | null
  created_at: string
  updated_at: string | null
}

export interface TranscriptionList {
  items: Transcription[]
  total: number
  page: number
  page_size: number
}

export interface DashboardStats {
  total_transcriptions: number
  total_duration: number
  total_words: number
  avg_duration: number
  recent_transcriptions: Transcription[]
  language_distribution: Record<string, number>
}

const API_HOST = import.meta.env.VITE_BACKEND_URL || ""
const BASE = `${API_HOST}/api/transcriptions`

async function request<T>(url: string, opts?: RequestInit): Promise<T> {
  const res = await fetch(url, { headers: { "Content-Type": "application/json" }, ...opts })
  if (!res.ok) {
    const body = await res.text()
    throw new Error(body || res.statusText)
  }
  return res.json()
}

export const api = {
  listTranscriptions: (page = 1, search = "", sortBy = "created_at", sortOrder = "desc") =>
    request<TranscriptionList>(`${BASE}?page=${page}&page_size=20&search=${search}&sort_by=${sortBy}&sort_order=${sortOrder}`),

  getTranscription: (id: string) => request<Transcription>(`${BASE}/${id}`),

  createTranscription: (data: { title: string; transcription_text: string; language_detected?: string; duration_seconds?: number }) =>
    request<Transcription>(BASE, { method: "POST", body: JSON.stringify(data) }),

  updateTranscription: (id: string, data: { title?: string; transcription_text?: string }) =>
    request<Transcription>(`${BASE}/${id}`, { method: "PUT", body: JSON.stringify(data) }),

  deleteTranscription: (id: string) => request<{ message: string }>(`${BASE}/${id}`, { method: "DELETE" }),

  getDashboardStats: () => request<DashboardStats>(`${BASE}/stats/dashboard`),

  getHealth: () => request<{ status: string; model: Record<string, unknown> }>(`${API_HOST}/api/health`),
}
