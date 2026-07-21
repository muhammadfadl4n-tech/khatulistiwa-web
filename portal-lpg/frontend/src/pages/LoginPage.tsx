import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { login } from '@/lib/api'
import { Fuel } from 'lucide-react'

export default function LoginPage() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(username, password)
      window.location.href = '/'
    } catch (err: any) {
      setError(err.message || 'Login gagal')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <Card className="w-full max-w-sm bg-card border-border">
        <CardHeader className="text-center">
          <div className="flex justify-center mb-3">
            <div className="h-12 w-12 rounded-xl bg-primary/15 flex items-center justify-center">
              <Fuel className="h-6 w-6 text-primary" />
            </div>
          </div>
          <CardTitle className="text-xl text-foreground">Portal LPG</CardTitle>
          <CardDescription className="text-muted-foreground">
            Masuk untuk mengakses dashboard LPG
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="bg-destructive/10 border border-destructive/20 text-destructive text-sm px-4 py-2.5 rounded-lg">
                {error}
              </div>
            )}
            <div className="space-y-2">
              <label className="text-sm text-muted-foreground">Username</label>
              <Input
                value={username}
                onChange={e => setUsername(e.target.value)}
                className="bg-secondary/50 border-input text-foreground"
                placeholder="admin"
                required
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm text-muted-foreground">Password</label>
              <Input
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                className="bg-secondary/50 border-input text-foreground"
                placeholder="••••••"
                required
              />
            </div>
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? 'Memproses...' : 'Masuk'}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
