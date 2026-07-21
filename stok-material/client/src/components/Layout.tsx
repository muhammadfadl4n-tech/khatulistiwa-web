import {
  ArrowDownToLine,
  ArrowUpFromLine,
  Clock,
  LayoutDashboard,
  LogOut,
  Menu,
  Package,
  UserRound,
  X,
} from "lucide-react"
import { useEffect, useRef, useState } from "react"
import { NavLink, Outlet, useNavigate } from "react-router-dom"
import { useAuth } from "../App"

const navItems = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/materials", label: "Materials", icon: Package },
  { to: "/incoming", label: "Barang Masuk", icon: ArrowDownToLine },
  { to: "/outgoing", label: "Barang Keluar", icon: ArrowUpFromLine },
  { to: "/mutations", label: "Histori", icon: Clock },
]

function NavLinks({ onNavClick }: { onNavClick?: () => void }) {
  const linkClass = ({ isActive }: { isActive: boolean }) =>
    [
      "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-semibold transition-all duration-200",
      isActive
        ? "bg-gradient-to-r from-blue-500 to-blue-600 text-white shadow-lg shadow-blue-500/20"
        : "text-slate-400 hover:bg-slate-800/80 hover:text-slate-100",
    ].join(" ")

  return (
    <>
      {navItems.map((item) => {
        const Icon = item.icon
        return (
          <NavLink key={item.to} to={item.to} end={item.to === "/"} className={linkClass} onClick={onNavClick}>
            <Icon size={18} />
            <span>{item.label}</span>
          </NavLink>
        )
      })}
    </>
  )
}

function Layout() {
  const [mobileOpen, setMobileOpen] = useState(false)
  const sidebarRef = useRef<HTMLDivElement>(null)
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const closeNav = () => setMobileOpen(false)

  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (sidebarRef.current && !sidebarRef.current.contains(e.target as Node)) {
        setMobileOpen(false)
      }
    }
    if (mobileOpen) document.addEventListener("mousedown", handleClick)
    return () => document.removeEventListener("mousedown", handleClick)
  }, [mobileOpen])

  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setMobileOpen(false)
    }
    if (mobileOpen) document.addEventListener("keydown", handleKey)
    return () => document.removeEventListener("keydown", handleKey)
  }, [mobileOpen])

  const handleLogout = () => {
    logout()
    navigate("/login", { replace: true })
  }

  return (
    <div className="min-h-screen bg-[#0f172a] text-[#e8edf5]">
      {/* ====== DESKTOP SIDEBAR ====== */}
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-[240px] flex-col border-r border-slate-800 bg-[#0f172a] lg:flex">
        {/* Logo */}
        <div className="flex h-16 shrink-0 items-center gap-3 border-b border-slate-800 px-5">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500 to-blue-600 text-white shadow-lg shadow-blue-500/20">
            <Package size={22} />
          </div>
          <div className="leading-tight">
            <p className="text-sm font-bold text-white">Stok Material</p>
            <p className="text-[11px] font-medium text-blue-300/80">Promo Management</p>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-5">
          <NavLinks />
        </nav>

        {/* User + Logout */}
        <div className="shrink-0 border-t border-slate-800 p-3">
          <div className="mb-2 flex items-center gap-3 rounded-lg px-3 py-2">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-slate-700 text-xs font-bold text-slate-300">
              {(user?.name || user?.username || "?").charAt(0).toUpperCase()}
            </div>
            <div className="min-w-0 leading-tight">
              <p className="truncate text-sm font-semibold text-slate-200">{user?.name || user?.username}</p>
              <p className="truncate text-[11px] text-slate-500">Admin</p>
            </div>
          </div>
          <button
            type="button"
            onClick={handleLogout}
            className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-semibold text-slate-400 transition-all duration-200 hover:bg-red-500/10 hover:text-red-300"
          >
            <LogOut size={18} />
            Logout
          </button>
        </div>
      </aside>

      {/* ====== MOBILE OVERLAY ====== */}
      {mobileOpen && <div className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden animate-fade-in" />}

      {/* ====== MOBILE DRAWER ====== */}
      <aside
        ref={sidebarRef}
        className={`fixed inset-y-0 left-0 z-50 flex w-[260px] flex-col border-r border-slate-800 bg-[#0f172a] transition-transform duration-300 ease-out lg:hidden ${
          mobileOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        {/* Drawer header (logo + close) */}
        <div className="flex h-16 shrink-0 items-center justify-between border-b border-slate-800 px-5">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500 to-blue-600 text-white shadow-lg shadow-blue-500/20">
              <Package size={22} />
            </div>
            <div className="leading-tight">
              <p className="text-sm font-bold text-white">Stok Material</p>
              <p className="text-[11px] font-medium text-blue-300/80">Promo Management</p>
            </div>
          </div>
          <button
            type="button"
            onClick={closeNav}
            className="flex h-9 w-9 items-center justify-center rounded-lg text-slate-400 hover:bg-slate-800 hover:text-white"
            aria-label="Tutup menu"
          >
            <X size={20} />
          </button>
        </div>

        {/* Nav (no duplikat logo!) */}
        <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-5">
          <NavLinks onNavClick={closeNav} />
        </nav>

        {/* User + Logout */}
        <div className="shrink-0 border-t border-slate-800 p-3">
          <div className="mb-2 flex items-center gap-3 rounded-lg px-3 py-2">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-slate-700 text-xs font-bold text-slate-300">
              {(user?.name || user?.username || "?").charAt(0).toUpperCase()}
            </div>
            <div className="min-w-0 leading-tight">
              <p className="truncate text-sm font-semibold text-slate-200">{user?.name || user?.username}</p>
              <p className="truncate text-[11px] text-slate-500">Admin</p>
            </div>
          </div>
          <button
            type="button"
            onClick={handleLogout}
            className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-semibold text-slate-400 transition-all duration-200 hover:bg-red-500/10 hover:text-red-300"
          >
            <LogOut size={18} />
            Logout
          </button>
        </div>
      </aside>

      {/* ====== MAIN CONTENT ====== */}
      <div className="min-h-screen lg:pl-[240px]">
        {/* Top bar */}
        <header className="sticky top-0 z-20 flex h-14 items-center justify-between border-b border-slate-800 bg-[#0f172a]/90 px-4 backdrop-blur-md lg:px-8">
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setMobileOpen(true)}
              className="flex h-9 w-9 items-center justify-center rounded-lg text-slate-400 hover:bg-slate-800 hover:text-white lg:hidden"
              aria-label="Buka menu"
            >
              <Menu size={20} />
            </button>
            <h1 className="text-sm font-bold tracking-tight text-white lg:text-base">
              Stok Material Promo
            </h1>
          </div>
          <div className="flex items-center gap-3">
            <div className="hidden items-center gap-2 rounded-lg border border-slate-700/50 bg-slate-800/50 px-3 py-1.5 sm:flex">
              <UserRound size={14} className="text-blue-300" />
              <span className="text-sm font-semibold text-slate-200">{user?.name || user?.username}</span>
            </div>
            <button
              type="button"
              onClick={handleLogout}
              className="flex h-9 w-9 items-center justify-center rounded-lg text-slate-400 hover:bg-red-500/10 hover:text-red-300 lg:hidden"
              aria-label="Logout"
            >
              <LogOut size={18} />
            </button>
          </div>
        </header>

        <main className="animate-fade-in px-4 py-5 sm:px-6 lg:px-8">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

export default Layout
