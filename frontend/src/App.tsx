import { Routes, Route } from "react-router-dom"
import Layout from "@/components/Layout"
import RecordPage from "@/pages/RecordPage"
import HistoryPage from "@/pages/HistoryPage"
import TranscriptionDetailPage from "@/pages/TranscriptionDetailPage"
import DashboardPage from "@/pages/DashboardPage"

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<RecordPage />} />
        <Route path="/history" element={<HistoryPage />} />
        <Route path="/transcription/:id" element={<TranscriptionDetailPage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
      </Routes>
    </Layout>
  )
}
