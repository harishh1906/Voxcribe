import { NavLink } from "react-router-dom"
import { Mic, ClipboardList, BarChart3, AudioWaveform } from "lucide-react"
import { cn } from "@/lib/utils"

const links = [
  { to: "/", label: "Record", icon: Mic },
  { to: "/history", label: "History", icon: ClipboardList },
  { to: "/dashboard", label: "Dashboard", icon: BarChart3 },
]

export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex flex-col md:flex-row h-screen w-full bg-white text-gray-900 overflow-hidden">
      {/* Mobile Top Header */}
      <header className="md:hidden flex items-center justify-between px-4 py-3 border-b bg-white/95 backdrop-blur sticky top-0 z-30 shrink-0">
        <div className="flex items-center gap-2">
          <AudioWaveform className="h-5 w-5 text-primary" />
          <span className="font-bold text-base tracking-tight">Voxcribe</span>
        </div>
        <span className="text-xs text-muted-foreground bg-gray-100 px-2 py-0.5 rounded font-mono">Hinglish AI</span>
      </header>

      {/* Desktop Sidebar */}
      <aside className="hidden md:flex w-56 shrink-0 border-r bg-gray-50/60 flex-col">
        <div className="flex items-center gap-2 px-5 py-5 border-b">
          <AudioWaveform className="h-6 w-6 text-primary" />
          <span className="font-bold text-lg tracking-tight">Voxcribe</span>
        </div>
        <nav className="flex-1 px-3 py-4 space-y-1">
          {links.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              end
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                  isActive ? "bg-primary/10 text-primary" : "text-muted-foreground hover:bg-accent"
                )
              }
            >
              <l.icon className="h-4 w-4" />
              {l.label}
            </NavLink>
          ))}
        </nav>
        <div className="px-5 py-4 border-t text-xs text-muted-foreground flex justify-between items-center">
          <span>v1.0.0</span>
          <span className="text-[10px] bg-primary/10 text-primary px-1.5 py-0.5 rounded font-medium">Hinglish</span>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 overflow-y-auto p-4 pb-28 md:p-6 md:pb-6 lg:p-10">
        {children}
      </main>

      {/* Mobile Bottom Navigation Bar */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 z-40 bg-white/95 backdrop-blur border-t flex justify-around items-center py-1.5 px-3 shadow-lg">
        {links.map((l) => (
          <NavLink
            key={l.to}
            to={l.to}
            end
            className={({ isActive }) =>
              cn(
                "flex flex-col items-center justify-center flex-1 py-1 rounded-lg text-xs font-medium transition-colors",
                isActive ? "text-primary font-semibold" : "text-muted-foreground hover:text-gray-900"
              )
            }
          >
            <l.icon className="h-5 w-5 mb-0.5" />
            <span>{l.label}</span>
          </NavLink>
        ))}
      </nav>
    </div>
  )
}
