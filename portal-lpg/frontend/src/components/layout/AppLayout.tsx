import { type ReactNode, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import { Button } from '@/components/ui/button'
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet'
import {
  LayoutDashboard, Fuel, Users, MapPin, LogOut,
  ChevronLeft, Menu,
} from 'lucide-react'
import { cn } from '@/lib/utils'

const navItems = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/lpg', label: 'LPG', icon: Fuel },
  { to: '/agen', label: 'Agen', icon: Users },
  { to: '/map', label: 'Map', icon: MapPin },
]

export default function AppLayout({ children }: { children: ReactNode }) {
  const [collapsed, setCollapsed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const { logout } = useAuth()
  const location = useLocation()

  const sidebarContent = (
    <div className="flex flex-col h-full">
      {/* Brand */}
      <div className="flex items-center gap-2.5 px-4 h-14 border-b border-border shrink-0">
        <div className="h-7 w-7 rounded-lg bg-primary/15 flex items-center justify-center">
          <Fuel className="h-3.5 w-3.5 text-primary" />
        </div>
        {!collapsed && (
          <span className="font-bold text-sm tracking-tight">Portal LPG</span>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-3 space-y-0.5 px-2 overflow-y-auto">
        {navItems.map((item) => (
          <Link
            key={item.to}
            to={item.to}
            onClick={() => setMobileOpen(false)}
            className={cn(
              'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
              location.pathname === item.to
                ? 'bg-primary/15 text-primary'
                : 'text-muted-foreground hover:bg-accent hover:text-foreground'
            )}
          >
            <item.icon className="h-4 w-4 shrink-0" />
            {!collapsed && <span className="truncate">{item.label}</span>}
          </Link>
        ))}
      </nav>

      {/* Logout */}
      <div className="border-t border-border p-3 shrink-0">
        <button
          onClick={logout}
          className={cn(
            'flex items-center gap-3 w-full px-3 py-2.5 rounded-lg text-sm font-medium text-muted-foreground hover:bg-destructive/10 hover:text-destructive transition-colors',
            collapsed && 'justify-center'
          )}
        >
          <LogOut className="h-4 w-4 shrink-0" />
          {!collapsed && <span>Logout</span>}
        </button>
      </div>
    </div>
  )

  return (
    <div className="flex min-h-screen bg-background">
      {/* Desktop sidebar */}
      <aside
        className={cn(
          'hidden md:flex flex-col border-r border-border bg-sidebar transition-all duration-300',
          collapsed ? 'w-16' : 'w-56'
        )}
      >
        {sidebarContent}

        {/* Collapse toggle */}
        <div className="border-t border-border p-2 shrink-0">
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="flex items-center justify-center h-8 w-full rounded-md hover:bg-accent text-muted-foreground"
          >
            {collapsed ? <ChevronLeft className="h-3.5 w-3.5" /> : <ChevronLeft className="h-3.5 w-3.5" />}
          </button>
        </div>
      </aside>

      {/* Mobile bottom nav */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 z-50 bg-sidebar border-t border-border flex items-center justify-around h-16 px-2 safe-area-bottom">
        {navItems.map((item) => (
          <Link
            key={item.to}
            to={item.to}
            className={cn(
              'flex flex-col items-center justify-center gap-0.5 py-1 px-3 rounded-lg transition-colors min-w-0 flex-1',
              location.pathname === item.to
                ? 'text-primary'
                : 'text-muted-foreground'
            )}
          >
            <item.icon className="h-5 w-5" />
            <span className="text-[10px] font-medium leading-tight">{item.label}</span>
          </Link>
        ))}
        <button
          onClick={logout}
          className="flex flex-col items-center justify-center gap-0.5 py-1 px-3 rounded-lg text-muted-foreground min-w-0 flex-1"
        >
          <LogOut className="h-5 w-5" />
          <span className="text-[10px] font-medium leading-tight">Logout</span>
        </button>
      </nav>

      {/* Mobile hamburger (visible on very small screens as an alternative) */}
      <div className="md:hidden fixed top-0 left-0 right-0 z-40 bg-sidebar/95 backdrop-blur border-b border-border flex items-center h-12 px-3">
        <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
          <SheetTrigger className="flex items-center justify-center h-8 w-8 rounded-md hover:bg-accent text-foreground -ml-1 cursor-pointer">
              <Menu className="h-5 w-5" />
          </SheetTrigger>
          <SheetContent side="left" className="w-64 p-0 bg-sidebar border-border">
            {sidebarContent}
          </SheetContent>
        </Sheet>
        <div className="flex items-center gap-2 ml-2">
          <Fuel className="h-4 w-4 text-primary" />
          <span className="font-bold text-sm">Portal LPG</span>
        </div>
      </div>

      {/* Main content */}
      <main className={cn(
        "flex-1 overflow-auto",
        "md:pt-0 pt-12 pb-16 md:pb-0"  /* padding for mobile header + bottom nav */
      )}>
        <div className="p-3 md:p-6 max-w-7xl mx-auto">
          {children}
        </div>
      </main>
    </div>
  )
}
