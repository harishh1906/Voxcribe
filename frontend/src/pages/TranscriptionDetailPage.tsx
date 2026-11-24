import { useState } from "react"
import { useParams, useNavigate } from "react-router-dom"
import { ArrowLeft, Copy, Download, Pencil, Save, Trash2, Clock, Globe, FileText } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent } from "@/components/ui/card"
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger,
} from "@/components/ui/alert-dialog"
import { useTranscription, useUpdateTranscription, useDeleteTranscription } from "@/hooks/useTranscriptions"
import { formatDuration } from "@/lib/utils"

export default function TranscriptionDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { data: t, isLoading } = useTranscription(id!)
  const updateMut = useUpdateTranscription()
  const deleteMut = useDeleteTranscription()
  const [editing, setEditing] = useState(false)
  const [editTitle, setEditTitle] = useState("")
  const [editText, setEditText] = useState("")
  const [copied, setCopied] = useState(false)

  if (isLoading) return <p className="text-center py-12 text-muted-foreground">Loading…</p>
  if (!t) return <p className="text-center py-12 text-muted-foreground">Not found</p>

  const startEdit = () => { setEditTitle(t.title); setEditText(t.transcription_text); setEditing(true) }
  const saveEdit = () => {
    updateMut.mutate({ id: t.id, data: { title: editTitle, transcription_text: editText } }, { onSuccess: () => setEditing(false) })
  }
  const handleCopy = () => { navigator.clipboard.writeText(t.transcription_text); setCopied(true); setTimeout(() => setCopied(false), 2000) }
  const handleDownload = () => {
    const blob = new Blob([t.transcription_text], { type: "text/plain" })
    const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = `${t.title}.txt`; a.click()
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <Button variant="ghost" size="sm" onClick={() => navigate("/history")} className="gap-1">
        <ArrowLeft className="h-4 w-4" />Back
      </Button>

      {/* Title */}
      {editing ? (
        <Input value={editTitle} onChange={(e) => setEditTitle(e.target.value)} className="text-xl font-bold" />
      ) : (
        <h1 className="text-2xl font-bold tracking-tight">{t.title}</h1>
      )}

      {/* Meta */}
      <div className="flex items-center gap-3 text-sm text-muted-foreground flex-wrap">
        <span className="flex items-center gap-1"><Clock className="h-4 w-4" />{formatDuration(t.duration_seconds)}</span>
        <span className="flex items-center gap-1"><FileText className="h-4 w-4" />{t.word_count} words</span>
        {t.language_detected && <Badge variant="outline" className="gap-1"><Globe className="h-3 w-3" />{t.language_detected}</Badge>}
        <span>{new Date(t.created_at).toLocaleString()}</span>
      </div>

      {/* Text */}
      <Card>
        <CardContent className="p-4">
          {editing ? (
            <Textarea value={editText} onChange={(e) => setEditText(e.target.value)} className="min-h-[300px] text-base" />
          ) : (
            <div className="min-h-[200px] text-base leading-relaxed whitespace-pre-wrap">
              {t.transcription_text || <span className="text-muted-foreground">Empty transcription</span>}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Actions */}
      <div className="flex flex-wrap gap-2">
        {editing ? (
          <>
            <Button onClick={saveEdit} disabled={updateMut.isPending}><Save className="h-4 w-4 mr-2" />{updateMut.isPending ? "Saving…" : "Save"}</Button>
            <Button variant="outline" onClick={() => setEditing(false)}>Cancel</Button>
          </>
        ) : (
          <>
            <Button variant="outline" size="sm" onClick={startEdit}><Pencil className="h-4 w-4 mr-2" />Edit</Button>
            <Button variant="outline" size="sm" onClick={handleCopy}><Copy className="h-4 w-4 mr-2" />{copied ? "Copied!" : "Copy"}</Button>
            <Button variant="outline" size="sm" onClick={handleDownload}><Download className="h-4 w-4 mr-2" />Download</Button>
            <AlertDialog>
              <AlertDialogTrigger asChild>
                <Button variant="destructive" size="sm"><Trash2 className="h-4 w-4 mr-2" />Delete</Button>
              </AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle>Delete this transcription?</AlertDialogTitle>
                  <AlertDialogDescription>This cannot be undone.</AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel>Cancel</AlertDialogCancel>
                  <AlertDialogAction className="bg-destructive text-destructive-foreground" onClick={() => deleteMut.mutate(t.id, { onSuccess: () => navigate("/history") })}>Delete</AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          </>
        )}
      </div>
    </div>
  )
}
