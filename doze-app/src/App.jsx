import { useState } from 'react'
import './index.css'

function App() {
  const [page, setPage] = useState('dashboard')
  const [selectedTask, setSelectedTask] = useState(null)

  return (
    <div style={{ maxWidth: 420, margin: '0 auto', minHeight: '100vh', background: 'var(--color-bg)', position: 'relative', paddingBottom: 80 }}>
      {page === 'dashboard' && <Dashboard onCreateTask={() => setPage('create')} onTaskClick={(t) => setSelectedTask(t)} />}
      {page === 'create' && <CreateTask onBack={() => setPage('dashboard')} />}
      {page === 'search' && <SearchPage onBack={() => setPage('dashboard')} onTaskClick={(t) => setSelectedTask(t)} />}
      {page === 'favorites' && <FavoritesPage onBack={() => setPage('dashboard')} onTaskClick={(t) => setSelectedTask(t)} />}
      {page === 'profile' && <ProfilePage onBack={() => setPage('dashboard')} />}

      {/* Task Detail Modal */}
      {selectedTask && (
        <TaskDetail task={selectedTask} onClose={() => setSelectedTask(null)} />
      )}

      <BottomNav page={page} setPage={setPage} />
    </div>
  )
}

// ── Task Data ─────────────────────────────────────────────
const TASKS = [
  { id: 1, variant: 'success', title: 'Desain Dribbble Shot Februari', date: '26 Feb', time: '10:15pm', tasks: '3/5', total: 5, done: 3, comments: 12, desc: 'Menyelesaikan desain Dribbble shot untuk konsep dashboard analitik yang modern dan interaktif.' },
  { id: 2, variant: 'warning', title: 'Pengembangan Fitur Login', date: '28 Feb', time: '09:00am', tasks: '2/4', total: 4, done: 2, comments: 8, desc: 'Implementasi autentikasi OAuth2 dengan Google dan email/password.' },
  { id: 3, variant: 'danger', title: 'Review Pull Request', date: '01 Mar', time: '11:30am', tasks: '1/3', total: 3, done: 1, comments: 5, desc: 'Review PR dari tim frontend terkait refactor komponen button dan modal.' },
  { id: 4, variant: 'success', title: 'Meeting dengan Tim Design', date: '02 Mar', time: '02:00pm', tasks: '4/6', total: 6, done: 4, comments: 3, desc: 'Diskusi progress design system komponen dashboard.' },
  { id: 5, variant: 'warning', title: 'Optimasi Database Query', date: '03 Mar', time: '04:00pm', tasks: '1/5', total: 5, done: 1, comments: 6, desc: 'Optimasi query lambat di halaman laporan dan analitik.' },
  { id: 6, variant: 'danger', title: 'Bug Fix — Filter Tanggal', date: '04 Mar', time: '09:30am', tasks: '0/2', total: 2, done: 0, comments: 4, desc: 'Filter tanggal di halaman transaksi tidak bekerja untuk range lintas bulan.' },
]

// ── Dashboard ─────────────────────────────────────────────
function Dashboard({ onCreateTask, onTaskClick }) {
  return (
    <div className="page">
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 24px' }}>
        <button className="pill-btn primary" onClick={onCreateTask}>
          <span style={{ width: 20, height: 20, borderRadius: 'var(--radius-pill)', background: 'var(--color-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#1a1c1e', fontSize: 16, fontWeight: 700, lineHeight: 1 }}>+</span>
          Create New Task
        </button>
        <div className="avatar" onClick={() => onTaskClick && onTaskClick('profile')} style={{ cursor: 'pointer' }}>
          <span style={{ fontSize: 16, color: 'var(--color-text-secondary)' }}>👤</span>
        </div>
      </header>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', padding: '16px 24px' }}>
        <h1 style={{ fontSize: 30, fontWeight: 600, color: '#fff', letterSpacing: '-0.025em', margin: 0 }}>Manage Your Task</h1>
      </div>

      <DateScroller />

      <div style={{ padding: '0 24px 120px' }}>
        {TASKS.slice(0, 4).map(task => (
          <TaskCard key={task.id} {...task} onClick={() => onTaskClick(task)} />
        ))}
      </div>
    </div>
  )
}

// ── Search Page ───────────────────────────────────────────
function SearchPage({ onBack, onTaskClick }) {
  const [query, setQuery] = useState('')
  const filtered = TASKS.filter(t =>
    t.title.toLowerCase().includes(query.toLowerCase())
  )
  return (
    <div className="page" style={{ minHeight: '100vh' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '16px 24px', borderBottom: '1px solid var(--color-border)' }}>
        <button onClick={onBack} style={{ background: 'none', border: 'none', color: 'var(--color-text)', cursor: 'pointer', fontSize: 24, padding: 0 }}>←</button>
        <input
          autoFocus
          value={query}
          onChange={e => setQuery(e.target.value)}
          placeholder="Cari task..."
          style={{ flex: 1, background: 'var(--color-surface)', border: 'none', borderRadius: 'var(--radius-pill)', padding: '12px 16px', color: 'var(--color-text)', fontFamily: 'inherit', fontSize: 14, outline: 'none' }}
        />
      </div>
      <div style={{ padding: '16px 24px 120px' }}>
        {filtered.length === 0 ? (
          <p style={{ textAlign: 'center', color: 'var(--color-text-secondary)', marginTop: 40, fontSize: 14 }}>
            {query ? 'Tidak ada task ditemukan' : 'Cari task berdasarkan judul...'}
          </p>
        ) : filtered.map(task => (
          <TaskCard key={task.id} {...task} onClick={() => onTaskClick(task)} compact />
        ))}
      </div>
    </div>
  )
}

// ── Favorites Page ─────────────────────────────────────────
function FavoritesPage({ onBack, onTaskClick }) {
  const [favs, setFavs] = useState([1, 3, 5])
  const favTasks = TASKS.filter(t => favs.includes(t.id))
  const toggleFav = (id) => {
    setFavs(prev => prev.includes(id) ? prev.filter(f => f !== id) : [...prev, id])
  }
  return (
    <div className="page" style={{ minHeight: '100vh' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 16, padding: '16px 24px', borderBottom: '1px solid var(--color-border)' }}>
        <button onClick={onBack} style={{ background: 'none', border: 'none', color: 'var(--color-text)', cursor: 'pointer', fontSize: 24, padding: 0 }}>←</button>
        <h2 style={{ margin: 0, fontSize: 20, fontWeight: 600, color: 'var(--color-text)' }}>Favorit</h2>
        <span style={{ fontSize: 12, color: 'var(--color-text-secondary)' }}>{favs.length} task</span>
      </div>
      <div style={{ padding: '16px 24px 120px' }}>
        {favTasks.map(task => (
          <div key={task.id} style={{ position: 'relative' }}>
            <TaskCard {...task} onClick={() => onTaskClick(task)} />
            <button
              onClick={(e) => { e.stopPropagation(); toggleFav(task.id); }}
              style={{ position: 'absolute', top: 12, right: 12, background: 'none', border: 'none', fontSize: 20, cursor: 'pointer', zIndex: 2 }}
            >❤️</button>
          </div>
        ))}
        {favTasks.length === 0 && (
          <p style={{ textAlign: 'center', color: 'var(--color-text-secondary)', marginTop: 40, fontSize: 14 }}>
            Belum ada task favorit. Tap ❤️ di task untuk menambahkannya.
          </p>
        )}
      </div>
    </div>
  )
}

// ── Profile Page ──────────────────────────────────────────
function ProfilePage({ onBack }) {
  const stats = {
    total: TASKS.length,
    completed: TASKS.filter(t => t.variant === 'success').length,
    inProgress: TASKS.filter(t => t.variant === 'warning').length,
    overdue: TASKS.filter(t => t.variant === 'danger').length,
  }
  return (
    <div className="page" style={{ minHeight: '100vh' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 16, padding: '16px 24px', borderBottom: '1px solid var(--color-border)' }}>
        <button onClick={onBack} style={{ background: 'none', border: 'none', color: 'var(--color-text)', cursor: 'pointer', fontSize: 24, padding: 0 }}>←</button>
        <h2 style={{ margin: 0, fontSize: 20, fontWeight: 600, color: 'var(--color-text)' }}>Profil</h2>
      </div>
      <div style={{ padding: '24px', textAlign: 'center' }}>
        <div style={{ width: 80, height: 80, borderRadius: 'var(--radius-pill)', background: 'var(--color-surface)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 36, margin: '0 auto 16px' }}>👤</div>
        <h2 style={{ margin: 0, fontSize: 22, fontWeight: 700, color: '#fff' }}>Ratu Cupid</h2>
        <p style={{ margin: '4px 0 24px', fontSize: 14, color: 'var(--color-text-secondary)' }}>Product Manager</p>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, marginBottom: 24 }}>
          {[
            { label: 'Total', value: stats.total, color: 'var(--color-text)' },
            { label: 'Selesai', value: stats.completed, color: 'var(--color-success)' },
            { label: 'Progress', value: stats.inProgress, color: 'var(--color-warning)' },
          ].map((s, i) => (
            <div key={i} style={{ background: 'var(--color-surface)', borderRadius: 'var(--radius-input)', padding: '16px 8px', textAlign: 'center' }}>
              <div style={{ fontSize: 24, fontWeight: 700, color: s.color }}>{s.value}</div>
              <div style={{ fontSize: 11, color: 'var(--color-text-secondary)', marginTop: 4 }}>{s.label}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

// ── Date Scroller ──────────────────────────────────────────
function DateScroller() {
  const [active, setActive] = useState(2)
  const dates = [
    { day: '21', month: 'Jul', label: 'Mon' },
    { day: '22', month: 'Jul', label: 'Tue' },
    { day: '23', month: 'Jul', label: 'Today', active: true },
    { day: '24', month: 'Jul', label: 'Thu' },
    { day: '25', month: 'Jul', label: 'Fri' },
    { day: '26', month: 'Jul', label: 'Sat' },
    { day: '27', month: 'Jul', label: 'Sun' },
  ]
  return (
    <div className="date-scroller">
      {dates.map((d, i) => (
        <button
          key={i}
          className={`date-chip${i === active ? ' active' : ''}`}
          onClick={() => setActive(i)}
        >
          {i === active ? (
            <><span className="date-num">{d.day} Jul</span><span className="date-label">Today</span></>
          ) : `${d.day} ${d.month}`}
        </button>
      ))}
    </div>
  )
}

// ── Task Card ──────────────────────────────────────────────
function TaskCard({ variant, title, date, time, tasks, comments, onClick, compact }) {
  return (
    <div className={`task-card ${variant}`} onClick={onClick} style={{ cursor: 'pointer' }}>
      <h3 style={{ fontSize: compact ? 18 : 22, fontWeight: 700, margin: 0, lineHeight: 1.2, width: '75%' }}>
        {title}
      </h3>
      <div className="share-btn" onClick={(e) => { e.stopPropagation(); alert('🔗 Link task disalin!') }} style={{ position: 'absolute', top: 20, right: 20 }}>
        ↗
      </div>
      <div style={{ display: 'flex', gap: 20, opacity: 0.7, marginTop: 16, marginBottom: compact ? 12 : 24 }}>
        <span style={{ fontSize: 14, fontWeight: 600 }}>📅 {date}</span>
        <span style={{ fontSize: 14, fontWeight: 600 }}>🕐 {time}</span>
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span style={{ fontSize: 16 }}>✓</span>
            <span style={{ fontSize: 14, fontWeight: 600 }}>{tasks}</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span style={{ fontSize: 14 }}>💬</span>
            <span style={{ fontSize: 14, fontWeight: 600 }}>{comments}</span>
          </div>
        </div>
        <div style={{ display: 'flex' }}>
          <div className="chip-avatar" style={{ marginRight: -6, border: '1px solid rgba(0,0,0,0.1)' }}>A</div>
          <div className="chip-avatar" style={{ marginRight: -6, border: '1px solid rgba(0,0,0,0.1)' }}>B</div>
          <div className="chip-avatar" style={{ border: '1px solid rgba(0,0,0,0.1)' }}>+2</div>
        </div>
      </div>
    </div>
  )
}

// ── Task Detail Modal ──────────────────────────────────────
function TaskDetail({ task, onClose }) {
  const pct = task.total > 0 ? Math.round(task.done / task.total * 100) : 0
  return (
    <div
      onClick={onClose}
      style={{
        position: 'fixed', inset: 0, zIndex: 200,
        background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)',
        display: 'flex', alignItems: 'flex-end', justifyContent: 'center',
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          width: '100%', maxWidth: 420,
          background: 'var(--color-surface-card)',
          borderRadius: '32px 32px 0 0',
          padding: '24px',
          animation: 'slideUp 0.3s ease',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 20 }}>
          <h2 style={{ margin: 0, fontSize: 22, fontWeight: 700, color: '#fff', flex: 1 }}>{task.title}</h2>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'var(--color-text-secondary)', fontSize: 24, cursor: 'pointer', padding: 0 }}>✕</button>
        </div>

        <p style={{ fontSize: 14, color: 'var(--color-text-secondary)', margin: '0 0 20px', lineHeight: 1.5 }}>{task.desc}</p>

        <div style={{ display: 'flex', gap: 12, marginBottom: 20 }}>
          <div style={{ background: 'var(--color-surface)', borderRadius: 'var(--radius-input)', padding: '12px 16px', flex: 1 }}>
            <div style={{ fontSize: 11, color: 'var(--color-text-secondary)', marginBottom: 4 }}>Deadline</div>
            <div style={{ fontSize: 14, fontWeight: 600, color: '#fff' }}>📅 {task.date}</div>
          </div>
          <div style={{ background: 'var(--color-surface)', borderRadius: 'var(--radius-input)', padding: '12px 16px', flex: 1 }}>
            <div style={{ fontSize: 11, color: 'var(--color-text-secondary)', marginBottom: 4 }}>Waktu</div>
            <div style={{ fontSize: 14, fontWeight: 600, color: '#fff' }}>🕐 {task.time}</div>
          </div>
        </div>

        <div style={{ marginBottom: 20 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
            <span style={{ fontSize: 13, fontWeight: 600, color: '#fff' }}>Progress</span>
            <span style={{ fontSize: 13, color: 'var(--color-text-secondary)' }}>{task.done}/{task.total} subtask ({pct}%)</span>
          </div>
          <div style={{ height: 6, borderRadius: 3, background: 'var(--color-surface)', overflow: 'hidden' }}>
            <div style={{ height: '100%', borderRadius: 3, background: task.variant === 'success' ? 'var(--color-success)' : task.variant === 'warning' ? 'var(--color-warning)' : 'var(--color-danger)', width: `${pct}%`, transition: 'width 0.5s ease' }} />
          </div>
        </div>

        <div style={{ display: 'flex', gap: 12, marginBottom: 20 }}>
          <div style={{ background: 'var(--color-surface)', borderRadius: 'var(--radius-input)', padding: '12px 16px', flex: 1 }}>
            <div style={{ fontSize: 11, color: 'var(--color-text-secondary)', marginBottom: 4 }}>Komentar</div>
            <div style={{ fontSize: 14, fontWeight: 600, color: '#fff' }}>💬 {task.comments}</div>
          </div>
          <div style={{ background: 'var(--color-surface)', borderRadius: 'var(--radius-input)', padding: '12px 16px', flex: 1 }}>
            <div style={{ fontSize: 11, color: 'var(--color-text-secondary)', marginBottom: 4 }}>Assignee</div>
            <div style={{ display: 'flex', marginTop: 4 }}>
              <div className="chip-avatar" style={{ marginRight: -6, border: '2px solid var(--color-surface)' }}>A</div>
              <div className="chip-avatar" style={{ marginRight: -6, border: '2px solid var(--color-surface)' }}>B</div>
              <div className="chip-avatar" style={{ border: '2px solid var(--color-surface)' }}>+2</div>
            </div>
          </div>
        </div>

        <button
          className="pill-btn full"
          onClick={() => alert('✅ Task ditandai selesai!')}
          style={{ marginBottom: 8 }}
        >
          Tandai Selesai
        </button>
      </div>
    </div>
  )
}

// ── Create Task ────────────────────────────────────────────
function CreateTask({ onBack }) {
  const [title, setTitle] = useState('')
  const [details, setDetails] = useState('')
  const [dueDate, setDueDate] = useState(2)

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!title.trim()) return
    alert(`✅ Task "${title}" berhasil dibuat!`)
    onBack()
  }

  return (
    <div className="page" style={{ minHeight: '100vh', background: 'var(--color-surface-card)' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 16, padding: '16px 24px', borderBottom: '1px solid var(--color-border)' }}>
        <button onClick={onBack} style={{ background: 'none', border: 'none', color: 'var(--color-text)', cursor: 'pointer', fontSize: 24, padding: 0 }}>←</button>
        <h2 style={{ margin: 0, fontSize: 20, fontWeight: 600, color: 'var(--color-text)' }}>Create New Task</h2>
      </div>

      <form onSubmit={handleSubmit} style={{ padding: '24px 24px 120px' }}>
        <h1 style={{ fontSize: 30, fontWeight: 700, color: '#fff', margin: '0 0 32px' }}>
          Hey, <br/>Create new task
        </h1>

        <div style={{ marginBottom: 24 }}>
          <label className="form-label">Task Title</label>
          <input className="form-input" type="text" value={title} onChange={e => setTitle(e.target.value)} placeholder="e.g. Desain Dashboard Baru" required />
        </div>

        <div style={{ marginBottom: 24 }}>
          <label className="form-label">Task Details</label>
          <textarea className="form-textarea" value={details} onChange={e => setDetails(e.target.value)} placeholder="Deskripsikan task secara detail..." rows={3} />
        </div>

        <div style={{ marginBottom: 24 }}>
          <label className="form-label">Due Date</label>
          <div style={{ display: 'flex', gap: 12, overflowX: 'auto', padding: '4px 0', scrollbarWidth: 'none' }}>
            {[['21 Jul'], ['22 Jul'], ['23 Jul', 'Today'], ['24 Jul'], ['25 Jul']].map((d, i) => (
              <button
                key={i}
                type="button"
                onClick={() => setDueDate(i)}
                style={{
                  flexShrink: 0,
                  border: 'none',
                  cursor: 'pointer',
                  fontFamily: 'inherit',
                  background: i === dueDate ? '#fff' : '#1a1c1e',
                  color: i === dueDate ? '#1a1c1e' : '#9ca3af',
                  borderRadius: i === dueDate ? 24 : 'var(--radius-pill)',
                  height: i === dueDate ? 44 : 40,
                  width: i === dueDate ? 70 : 'auto',
                  padding: i === dueDate ? 0 : '0 20px',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 14,
                  fontWeight: i === dueDate ? 700 : 500,
                  whiteSpace: 'pre-line',
                  lineHeight: 1.2,
                }}
              >
                {d[0]}{d[1] ? <span style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.05em', opacity: 0.8 }}>{d[1]}</span> : null}
              </button>
            ))}
          </div>
        </div>

        <div style={{ marginBottom: 24 }}>
          <label className="form-label">Assignee</label>
          <div style={{ display: 'flex', gap: 12, overflowX: 'auto', padding: '4px 0', scrollbarWidth: 'none' }}>
            <div className="chip" style={{ cursor: 'pointer', background: '#ffce54', color: '#1a1c1e' }}>
              <div className="chip-avatar" style={{ background: '#1a1c1e', color: '#ffce54' }}>A</div>
              Ahmad Fauzi
            </div>
            <div className="chip" style={{ cursor: 'pointer' }}>
              <div className="chip-avatar">S</div>
              Siti Nurhaliza
            </div>
            <button
              type="button"
              style={{
                width: 44, height: 44, borderRadius: 'var(--radius-pill)',
                background: '#1a1c1e', border: 'none', color: '#fff',
                cursor: 'pointer', fontSize: 20, flexShrink: 0,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}
            >+</button>
          </div>
        </div>

        <div style={{ marginBottom: 24 }}>
          <label className="form-label">Attachment</label>
          <div style={{ display: 'flex', gap: 12 }}>
            <div className="attachment-box" style={{ color: '#14b8a6', fontSize: 24 }}>📎</div>
            <div className="attachment-box" style={{ color: '#fff', fontSize: 24 }}>📄</div>
            <div className="attachment-box" style={{ color: '#60a5fa', fontSize: 24 }}>🖼</div>
          </div>
        </div>

        <div className="sticky-bottom">
          <button type="submit" className="pill-btn full">
            Create Task
          </button>
        </div>
      </form>
    </div>
  )
}

// ── Bottom Nav ─────────────────────────────────────────────
function BottomNav({ page, setPage }) {
  const tabs = [
    { id: 'dashboard', icon: '🏠', label: 'Home' },
    { id: 'search', icon: '🔍', label: 'Search' },
    { id: 'create', icon: '➕', label: 'Add' },
    { id: 'favorites', icon: '❤️', label: 'Heart' },
    { id: 'profile', icon: '👤', label: 'Profile' },
  ]
  return (
    <nav style={{
      position: 'fixed',
      bottom: 0,
      left: '50%',
      transform: 'translateX(-50%)',
      width: '100%',
      maxWidth: 420,
      background: '#2a2c2e',
      borderTopLeftRadius: 32,
      borderTopRightRadius: 32,
      display: 'flex',
      justifyContent: 'space-around',
      alignItems: 'center',
      padding: '8px 0 16px',
      zIndex: 100,
      boxShadow: '0 -4px 20px rgba(0,0,0,0.3)',
    }}>
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => setPage(tab.id)}
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 2,
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            color: page === tab.id ? '#ffce54' : '#9ca3af',
            fontSize: 10,
            fontFamily: 'inherit',
            transition: 'color 0.2s',
            padding: '4px 12px',
          }}
        >
          <span style={{ fontSize: 22 }}>{tab.icon}</span>
          <span>{tab.label}</span>
        </button>
      ))}
    </nav>
  )
}

export default App
