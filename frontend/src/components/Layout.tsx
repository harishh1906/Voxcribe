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
    <div className="flex h-screen">
      {/* Sidebar */}
      <aside className="w-56 shrink-0 border-r bg-gray-50/60 flex flex-col">
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
        <div className="px-5 py-4 border-t text-xs text-muted-foreground">v1.0.0</div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto p-6 lg:p-10">{children}</main>
    </div>
  )
}
