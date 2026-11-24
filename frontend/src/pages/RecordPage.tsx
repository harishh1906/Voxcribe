import { useState, useEffect, useCallback, useRef } from "react"
import { Mic, MicOff, Pause, Play, Copy, Download, Trash2, Save, Wifi, WifiOff, Globe } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent } from "@/components/ui/card"
import { useWebSocket } from "@/hooks/useWebSocket"
import { useAudioRecorder } from "@/hooks/useAudioRecorder"
import { useCreateTranscription } from "@/hooks/useTranscriptions"
import { formatDuration } from "@/lib/utils"

export default function RecordPage() {
  const [title, setTitle] = useState("Untitled Recording")
  const [transcription, setTranscription] = useState("")
  const [partialText, setPartialText] = useState("")
  const [language, setLanguage] = useState("")
  const [savedId, setSavedId] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)
  const textAreaRef = useRef<HTMLDivElement>(null)

  const { status: wsStatus, lastMessage, connect, disconnect, sendMessage } = useWebSocket()
  const createMutation = useCreateTranscription()

  // Audio chunk handler – sends base64 audio to backend via WS
  const onAudioChunk = useCallback(
    (b64: string) => {
      sendMessage({ type: "audio_chunk", data: { audio: b64 } })
    },
    [sendMessage]
  )

  const { startRecording, stopRecording, pauseRecording, resumeRecording, isRecording, isPaused, duration, audioLevel, error: micError } = useAudioRecorder(onAudioChunk)

  // Handle incoming WS messages
  useEffect(() => {
    if (!lastMessage) return
    const msg = lastMessage as { type: string; data: Record<string, unknown> }

    if (msg.type === "partial_transcription") {
      const d = msg.data as { text: string; language?: string }
      setPartialText(d.text)
      if (d.language) setLanguage(d.language)
    } else if (msg.type === "final_transcription") {
      const d = msg.data as { id: string; text: string; language?: string }
      setTranscription(d.text)
      setPartialText("")
      if (d.language) setLanguage(d.language)
      if (d.id) setSavedId(d.id)
    }
  }, [lastMessage])

  // Auto-scroll
  useEffect(() => {
    if (textAreaRef.current) textAreaRef.current.scrollTop = textAreaRef.current.scrollHeight
  }, [transcription, partialText])

  const handleStart = async () => {
    setSavedId(null)
    setTranscription("")
    setPartialText("")
    setLanguage("")
    connect()
    // small delay to let WS connect
    setTimeout(() => {
      sendMessage({ type: "start_recording" })
      startRecording()
    }, 500)
  }

  const handleStop = () => {
    stopRecording()
    sendMessage({ type: "stop_recording" })
    setTimeout(() => disconnect(), 2000)
  }

  const handlePause = () => {
    pauseRecording()
    sendMessage({ type: "pause_recording" })
  }

  const handleResume = () => {
    resumeRecording()
    sendMessage({ type: "resume_recording" })
  }

  const handleCopy = () => {
    const text = transcription + (partialText ? " " + partialText : "")
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleDownload = () => {
    const text = transcription + (partialText ? " " + partialText : "")
    const blob = new Blob([text], { type: "text/plain" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `${title}.txt`
    a.click()
    URL.revokeObjectURL(url)
  }

  const handleSave = () => {
    const text = transcription + (partialText ? " " + partialText : "")
    createMutation.mutate(
      { title, transcription_text: text, language_detected: language || undefined, duration_seconds: duration },
      { onSuccess: (t) => setSavedId(t.id) }
    )
  }

  const handleClear = () => {
    setTranscription("")
    setPartialText("")
    setLanguage("")
    setSavedId(null)
  }

  const displayText = transcription + (partialText ? " " + partialText : "")

  return (
    <div className="max-w-3xl mx-auto space-y-5 sm:space-y-7 px-1 sm:px-0">
      {/* Header */}
      <div>
        <h1 className="text-xl sm:text-2xl font-bold tracking-tight">New Recording</h1>
        <p className="text-muted-foreground text-xs sm:text-sm mt-0.5">Speak naturally — your words appear as Hinglish/English text in real time.</p>
      </div>

      {/* Title input */}
      <Input
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        placeholder="Recording title…"
        className="text-base sm:text-lg font-medium border-none shadow-none px-0 focus-visible:ring-0"
      />

      {/* Status bar */}
      <div className="flex items-center gap-2 flex-wrap text-xs sm:text-sm">
        <Badge variant={wsStatus === "connected" ? "default" : "outline"} className="gap-1 text-xs">
          {wsStatus === "connected" ? <Wifi className="h-3 w-3" /> : <WifiOff className="h-3 w-3" />}
          {wsStatus}
        </Badge>
        {language && (
          <Badge variant="secondary" className="gap-1 text-xs font-medium">
            <Globe className="h-3 w-3" />
            {language}
          </Badge>
        )}
        {isRecording && <Badge variant="destructive" className="text-xs">● Recording</Badge>}
        {isPaused && <Badge variant="outline" className="text-xs">Paused</Badge>}
        {savedId && <Badge variant="secondary" className="text-green-600 text-xs">✓ Saved</Badge>}
      </div>

      {/* Audio level bar */}
      {isRecording && (
        <div className="h-2 rounded-full bg-gray-100 overflow-hidden">
          <div
            className="h-full bg-primary rounded-full transition-all duration-100"
            style={{ width: `${Math.max(audioLevel * 100, 2)}%` }}
          />
        </div>
      )}

      {/* Mic button + controls */}
      <div className="flex flex-col items-center gap-3 sm:gap-4 my-2">
        <div className="relative">
          {isRecording && (
            <div className="absolute inset-0 rounded-full bg-red-400/30 animate-pulse-ring" />
          )}
          <button
            onClick={isRecording ? handleStop : handleStart}
            className={`relative z-10 h-16 w-16 sm:h-20 sm:w-20 rounded-full flex items-center justify-center transition-all shadow-lg active:scale-95 ${
              isRecording ? "bg-red-500 text-white hover:bg-red-600" : "bg-white border-2 border-gray-200 text-gray-700 hover:border-primary hover:text-primary"
            }`}
          >
            {isRecording ? <MicOff className="h-7 w-7 sm:h-8 sm:w-8" /> : <Mic className="h-7 w-7 sm:h-8 sm:w-8" />}
          </button>
        </div>

        <div className="flex items-center gap-3">
          {!isRecording ? (
            <Button onClick={handleStart} size="lg" className="px-6 text-sm sm:text-base">Start Recording</Button>
          ) : (
            <>
              <Button onClick={handleStop} variant="destructive" size="lg" className="px-5 text-sm sm:text-base">Stop</Button>
              {isPaused ? (
                <Button onClick={handleResume} variant="outline" size="lg" className="px-4 text-sm sm:text-base"><Play className="h-4 w-4 mr-1.5" />Resume</Button>
              ) : (
                <Button onClick={handlePause} variant="outline" size="lg" className="px-4 text-sm sm:text-base"><Pause className="h-4 w-4 mr-1.5" />Pause</Button>
              )}
            </>
          )}
        </div>

        {isRecording && <span className="text-xs sm:text-sm text-muted-foreground font-mono">{formatDuration(duration)}</span>}
      </div>

      {/* Error */}
      {micError && (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-md p-3 text-xs sm:text-sm">
          <strong>Microphone error:</strong> {micError}
        </div>
      )}

      {/* Transcription area */}
      <Card className="shadow-sm border-gray-200">
        <CardContent className="p-3 sm:p-5">
          <div ref={textAreaRef} className="min-h-[180px] max-h-[360px] sm:min-h-[220px] sm:max-h-[420px] overflow-y-auto text-sm sm:text-base leading-relaxed whitespace-pre-wrap">
            {displayText ? (
              <>
                <span>{transcription}</span>
                {partialText && <span className="text-muted-foreground italic"> {partialText}</span>}
              </>
            ) : (
              <span className="text-muted-foreground text-xs sm:text-sm">Start recording and speak in English, Hindi, or Hinglish…</span>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Action buttons (grid on small screens, flex on desktop) */}
      <div className="grid grid-cols-2 sm:flex sm:flex-wrap gap-2">
        <Button variant="outline" size="sm" onClick={handleCopy} disabled={!displayText} className="w-full sm:w-auto text-xs sm:text-sm">
          <Copy className="h-3.5 w-3.5 mr-1.5" />{copied ? "Copied!" : "Copy"}
        </Button>
        <Button variant="outline" size="sm" onClick={handleDownload} disabled={!displayText} className="w-full sm:w-auto text-xs sm:text-sm">
          <Download className="h-3.5 w-3.5 mr-1.5" />Download
        </Button>
        <Button variant="outline" size="sm" onClick={handleSave} disabled={!displayText || createMutation.isPending} className="w-full sm:w-auto text-xs sm:text-sm">
          <Save className="h-3.5 w-3.5 mr-1.5" />{createMutation.isPending ? "Saving…" : "Save"}
        </Button>
        <Button variant="ghost" size="sm" onClick={handleClear} disabled={!displayText} className="w-full sm:w-auto text-xs sm:text-sm text-muted-foreground">
          <Trash2 className="h-3.5 w-3.5 mr-1.5" />Clear
        </Button>
      </div>
    </div>
  )
}
