import { createContext, useContext, useState, useEffect, type ReactNode } from 'react'
import { checkAuth, logout as apiLogout } from '@/lib/api'

interface AuthContextType {
  isAuthenticated: boolean
  isLoading: boolean
  check: () => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextType | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [isLoading, setIsLoading] = useState(true)

  const check = async () => {
    setIsLoading(true)
    const ok = await checkAuth()
    setIsAuthenticated(ok)
    setIsLoading(false)
  }

  useEffect(() => { check() }, [])

  const logout = () => apiLogout()

  return (
    <AuthContext.Provider value={{ isAuthenticated, isLoading, check, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
