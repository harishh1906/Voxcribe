import { useRef, useState, useCallback, useEffect } from "react"

export function useAudioRecorder(onChunk: (base64: string) => void) {
  const mediaRef = useRef<MediaRecorder | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const rafRef = useRef<number>(0)

  const [isRecording, setIsRecording] = useState(false)
  const [isPaused, setIsPaused] = useState(false)
  const [duration, setDuration] = useState(0)
  const [audioLevel, setAudioLevel] = useState(0)
  const [error, setError] = useState<string | null>(null)

  const startRecording = useCallback(async () => {
    setError(null)
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      streamRef.current = stream

      // Audio analyser for level visualisation
      const audioCtx = new AudioContext()
      const source = audioCtx.createMediaStreamSource(stream)
      const analyser = audioCtx.createAnalyser()
      analyser.fftSize = 256
      source.connect(analyser)
      analyserRef.current = analyser

      const updateLevel = () => {
        if (!analyserRef.current) return
        const data = new Uint8Array(analyserRef.current.frequencyBinCount)
        analyserRef.current.getByteFrequencyData(data)
        const avg = data.reduce((a, b) => a + b, 0) / data.length
        setAudioLevel(avg / 255)
        rafRef.current = requestAnimationFrame(updateLevel)
      }
      updateLevel()

      const recorder = new MediaRecorder(stream, { mimeType: "audio/webm;codecs=opus" })
      recorder.ondataavailable = async (e) => {
        if (e.data.size > 0) {
          const reader = new FileReader()
          reader.onloadend = () => {
            const result = reader.result as string
            const b64 = result.split(",")[1]
            if (b64) onChunk(b64)
          }
          reader.readAsDataURL(e.data)
        }
      }
      recorder.start(1000) // chunk every 1 second
      mediaRef.current = recorder
      setIsRecording(true)
      setIsPaused(false)
      setDuration(0)
      timerRef.current = setInterval(() => setDuration((d) => d + 1), 1000)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Microphone access denied"
      setError(msg)
    }
  }, [onChunk])

  const stopRecording = useCallback(() => {
    mediaRef.current?.stop()
    streamRef.current?.getTracks().forEach((t) => t.stop())
    if (timerRef.current) clearInterval(timerRef.current)
    cancelAnimationFrame(rafRef.current)
    setIsRecording(false)
    setIsPaused(false)
    setAudioLevel(0)
  }, [])

  const pauseRecording = useCallback(() => {
    if (mediaRef.current?.state === "recording") {
      mediaRef.current.pause()
      if (timerRef.current) clearInterval(timerRef.current)
      setIsPaused(true)
    }
  }, [])

  const resumeRecording = useCallback(() => {
    if (mediaRef.current?.state === "paused") {
      mediaRef.current.resume()
      timerRef.current = setInterval(() => setDuration((d) => d + 1), 1000)
      setIsPaused(false)
    }
  }, [])

  useEffect(() => () => {
    mediaRef.current?.stop()
    streamRef.current?.getTracks().forEach((t) => t.stop())
    if (timerRef.current) clearInterval(timerRef.current)
    cancelAnimationFrame(rafRef.current)
  }, [])

  return { startRecording, stopRecording, pauseRecording, resumeRecording, isRecording, isPaused, duration, audioLevel, error }
}
