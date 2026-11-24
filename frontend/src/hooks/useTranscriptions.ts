import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "@/lib/api"

export function useTranscriptions(page: number, search = "") {
  return useQuery({
    queryKey: ["transcriptions", page, search],
    queryFn: () => api.listTranscriptions(page, search),
  })
}

export function useTranscription(id: string) {
  return useQuery({
    queryKey: ["transcription", id],
    queryFn: () => api.getTranscription(id),
    enabled: !!id,
  })
}

export function useCreateTranscription() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: api.createTranscription,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["transcriptions"] }),
  })
}

export function useUpdateTranscription() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: { title?: string; transcription_text?: string } }) =>
      api.updateTranscription(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["transcriptions"] })
      qc.invalidateQueries({ queryKey: ["transcription"] })
    },
  })
}

export function useDeleteTranscription() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: api.deleteTranscription,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["transcriptions"] }),
  })
}

export function useDashboardStats() {
  return useQuery({
    queryKey: ["dashboard"],
    queryFn: api.getDashboardStats,
  })
}
