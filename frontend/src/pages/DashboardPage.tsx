import { useNavigate } from "react-router-dom"
import { Mic, Clock, FileText, BarChart3 } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { useDashboardStats } from "@/hooks/useTranscriptions"
import { formatDuration, timeAgo } from "@/lib/utils"

export default function DashboardPage() {
  const { data, isLoading } = useDashboardStats()
  const navigate = useNavigate()

  if (isLoading) return <p className="text-center py-12 text-muted-foreground">Loading…</p>
  if (!data) return null

  const stats = [
    { label: "Total Transcriptions", value: data.total_transcriptions, icon: Mic },
    { label: "Total Duration", value: formatDuration(data.total_duration), icon: Clock },
    { label: "Total Words", value: data.total_words.toLocaleString(), icon: FileText },
    { label: "Avg Duration", value: formatDuration(data.avg_duration), icon: BarChart3 },
  ]

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>

      {/* Stats grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        {stats.map((s) => (
          <Card key={s.label}>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                <s.icon className="h-4 w-4" />{s.label}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{s.value}</div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Language distribution */}
      {Object.keys(data.language_distribution).length > 0 && (
        <Card>
          <CardHeader><CardTitle className="text-base">Languages Detected</CardTitle></CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {Object.entries(data.language_distribution).map(([lang, count]) => (
                <Badge key={lang} variant="secondary" className="text-sm">
                  {lang}: {count}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Recent transcriptions */}
      <Card>
        <CardHeader><CardTitle className="text-base">Recent Transcriptions</CardTitle></CardHeader>
        <CardContent>
          {data.recent_transcriptions.length === 0 ? (
            <p className="text-muted-foreground text-sm">No transcriptions yet.</p>
          ) : (
            <div className="space-y-3">
              {data.recent_transcriptions.map((t) => (
                <div
                  key={t.id}
                  className="flex justify-between items-center p-3 rounded-md hover:bg-accent cursor-pointer transition-colors"
                  onClick={() => navigate(`/transcription/${t.id}`)}
                >
                  <div className="min-w-0">
                    <p className="font-medium truncate">{t.title}</p>
                    <p className="text-xs text-muted-foreground">{formatDuration(t.duration_seconds)} · {t.word_count} words</p>
                  </div>
                  <span className="text-xs text-muted-foreground shrink-0">{timeAgo(t.created_at)}</span>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
