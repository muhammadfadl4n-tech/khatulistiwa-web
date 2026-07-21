import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react"
import { Navigate, Route, Routes } from "react-router-dom"
import Layout from "./components/Layout"
import ProtectedRoute from "./components/ProtectedRoute"
import DashboardPage from "./pages/DashboardPage"
import IncomingPage from "./pages/IncomingPage"
import LoginPage from "./pages/LoginPage"
import MaterialsPage from "./pages/MaterialsPage"
import MutationsPage from "./pages/MutationsPage"
import OutgoingPage from "./pages/OutgoingPage"
import { api } from "./api"

export type User = {
  id?: string | number
  username: string
  name?: string
}

type AuthContextValue = {
  user: User | null
  isAuthenticated: boolean
  login: (user: User) => void
  logout: () => void
  loading: boolean
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function useAuth() {
  const value = useContext(AuthContext)
  if (!value) {
    throw new Error("useAuth must be used within AuthProvider")
  }
  return value
}

function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  // Restore session from cookie on mount
  useEffect(() => {
    const restore = async () => {
      try {
        const data = await api.get<{ user: User }>("/api/auth/me")
        setUser(data.user)
      } catch {
        // No valid session — stay logged out
      } finally {
        setLoading(false)
      }
    }
    void restore()
  }, [])

  const value = useMemo(
    () => ({
      user,
      isAuthenticated: Boolean(user),
      login: setUser,
      logout: () => setUser(null),
      loading,
    }),
    [user, loading],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route element={<ProtectedRoute />}>
          <Route element={<Layout />}>
            <Route index element={<DashboardPage />} />
            <Route path="materials" element={<MaterialsPage />} />
            <Route path="mutations" element={<MutationsPage />} />
            <Route path="incoming" element={<IncomingPage />} />
            <Route path="outgoing" element={<OutgoingPage />} />
          </Route>
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  )
}

export default App
