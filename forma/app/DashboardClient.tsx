"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

type QuestionType = "short" | "long" | "email" | "choice" | "rating" | "media";
type Question = {
  id: string;
  title: string;
  type: QuestionType;
  required: boolean;
  options?: string[];
};
type FormRecord = {
  id: string;
  title: string;
  description: string;
  status: "draft" | "published";
  questions: Question[];
  createdAt: number;
  updatedAt: number;
  responseCount: number;
  compressMedia: boolean;
};
type ResponseRecord = {
  id: string;
  answers: Record<string, string>;
  submittedAt: number;
};
type View =
  | "dashboard"
  | "forms"
  | "editor"
  | "preview"
  | "results"
  | "templates";

const templates = [
  {
    title: "Customer survey",
    description: "Collect satisfaction, product feedback and an NPS signal.",
    tone: "indigo",
    questions: 6,
  },
  {
    title: "Event registration",
    description: "Capture attendees, sessions and dietary preferences.",
    tone: "cyan",
    questions: 7,
  },
  {
    title: "Job application",
    description: "A focused applicant intake with role-specific questions.",
    tone: "amber",
    questions: 8,
  },
];

const typeLabels: Record<QuestionType, string> = {
  short: "Short answer",
  long: "Long answer",
  email: "Email",
  choice: "Multiple choice",
  rating: "Rating scale",
  media: "Upload media",
};

const uid = () => crypto.randomUUID();
const ago = (timestamp: number) => {
  const minutes = Math.max(1, Math.floor((Date.now() - timestamp) / 60000));
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
};

export default function DashboardClient({
  displayName,
  email,
}: {
  displayName: string;
  email: string;
}) {
  const [view, setView] = useState<View>("dashboard");
  const [forms, setForms] = useState<FormRecord[]>([]);
  const [activeId, setActiveId] = useState<string>("");
  const [draft, setDraft] = useState<FormRecord | null>(null);
  const [responses, setResponses] = useState<ResponseRecord[]>([]);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<"all" | "published" | "draft">("all");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [notice, setNotice] = useState("");
  const [menuOpen, setMenuOpen] = useState(false);

  const loadForms = useCallback(async () => {
    try {
      const data = (await fetch("/api/forms").then((r) => r.json())) as {
        forms: FormRecord[];
      };
      setForms(data.forms);
      if (!activeId && data.forms[0]) setActiveId(data.forms[0].id);
    } finally {
      setLoading(false);
    }
  }, [activeId]);

  useEffect(() => {
    loadForms();
  }, [loadForms]);

  const active = forms.find((form) => form.id === activeId) ?? forms[0];
  const totalResponses = forms.reduce(
    (sum, form) => sum + form.responseCount,
    0,
  );
  const published = forms.filter((form) => form.status === "published").length;
  const completion = forms.length
    ? Math.round((published / forms.length) * 100)
    : 0;

  const filtered = useMemo(
    () =>
      forms.filter((form) => {
        const matchesText = `${form.title} ${form.description}`
          .toLowerCase()
          .includes(search.toLowerCase());
        return matchesText && (filter === "all" || form.status === filter);
      }),
    [forms, search, filter],
  );

  function announce(message: string) {
    setNotice(message);
    window.setTimeout(() => setNotice(""), 2600);
  }

  function openPublicForm(form: FormRecord) {
    if (form.status !== "published")
      return announce("Publish this form before sharing it publicly");
    window.open(`/f/${form.id}`, "_blank", "noopener,noreferrer");
  }

  async function copyPublicLink(form: FormRecord) {
    if (form.status !== "published")
      return announce("Publish this form before copying its public link");
    await navigator.clipboard.writeText(
      `${window.location.origin}/f/${form.id}`,
    );
    announce("Public form link copied");
  }

  async function createForm(title = "Untitled form", questions?: Question[]) {
    const response = await fetch("/api/forms", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ title, questions }),
    });
    const data = (await response.json()) as { id: string };
    await loadForms();
    const newForm: FormRecord = {
      id: data.id,
      title,
      description: "",
      status: "draft",
      questions: questions ?? [
        {
          id: uid(),
          title: "Untitled question",
          type: "short",
          required: false,
        },
      ],
      createdAt: Date.now(),
      updatedAt: Date.now(),
      responseCount: 0,
      compressMedia: true,
    };
    setActiveId(data.id);
    setDraft(newForm);
    setView("editor");
  }

  function openEditor(form: FormRecord) {
    setActiveId(form.id);
    setDraft(structuredClone(form));
    setView("editor");
  }

  async function saveDraft(nextStatus?: "draft" | "published") {
    if (!draft) return;
    setSaving(true);
    const next = { ...draft, status: nextStatus ?? draft.status };
    await fetch("/api/forms", {
      method: "PATCH",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(next),
    });
    setDraft(next);
    await loadForms();
    setSaving(false);
    announce(
      nextStatus === "published"
        ? "Form published and ready to share"
        : "All changes saved",
    );
  }

  async function removeForm(form: FormRecord) {
    if (!window.confirm(`Delete “${form.title}” and all of its responses?`))
      return;
    await fetch(`/api/forms?id=${encodeURIComponent(form.id)}`, {
      method: "DELETE",
    });
    await loadForms();
    setView("forms");
    announce("Form deleted");
  }

  async function openResults(form: FormRecord) {
    setActiveId(form.id);
    setView("results");
    const data = (await fetch(
      `/api/responses?formId=${encodeURIComponent(form.id)}`,
    ).then((r) => r.json())) as { responses: ResponseRecord[] };
    setResponses(data.responses);
  }

  function updateQuestion(index: number, patch: Partial<Question>) {
    if (!draft) return;
    const questions = [...draft.questions];
    questions[index] = { ...questions[index], ...patch };
    setDraft({ ...draft, questions });
  }

  function moveQuestion(index: number, direction: -1 | 1) {
    if (!draft) return;
    const next = index + direction;
    if (next < 0 || next >= draft.questions.length) return;
    const questions = [...draft.questions];
    [questions[index], questions[next]] = [questions[next], questions[index]];
    setDraft({ ...draft, questions });
  }

  async function submitResponse(event: React.FormEvent) {
    event.preventDefault();
    if (!active) return;
    await fetch("/api/responses", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ formId: active.id, answers }),
    });
    setAnswers({});
    await loadForms();
    announce("Thanks — your response was recorded");
  }

  const nav = (target: View, label: string, mark: string) => (
    <button
      className={`nav-item ${view === target ? "active" : ""}`}
      onClick={() => {
        setView(target);
        setMenuOpen(false);
      }}
    >
      <span className="nav-mark">{mark}</span>
      <span>{label}</span>
    </button>
  );

  return (
    <div className="app-shell">
      <aside className={`sidebar ${menuOpen ? "open" : ""}`}>
        <button
          className="brand"
          onClick={() => setView("dashboard")}
          aria-label="Forma home"
        >
          <span className="brand-mark">
            <i></i>
            <i></i>
            <i></i>
          </span>
          <span>forma</span>
        </button>
        <nav aria-label="Main navigation">
          <p className="nav-label">Workspace</p>
          {nav("dashboard", "Dashboard", "⌂")}
          {nav("forms", "My forms", "▦")}
          {nav("templates", "Templates", "◇")}
          <p className="nav-label second">Manage</p>
          <button
            className="nav-item"
            onClick={() =>
              announce("Team collaboration is ready for your next workspace")
            }
          >
            <span className="nav-mark">♙</span>
            <span>Team</span>
            <span className="soon">Soon</span>
          </button>
          <button
            className="nav-item"
            onClick={() => announce("Workspace settings opened")}
          >
            <span className="nav-mark">⚙</span>
            <span>Settings</span>
          </button>
        </nav>
        <div className="sidebar-card">
          <span className="spark">✦</span>
          <strong>Make every question count.</strong>
          <p>Use clear language and keep each form focused on one goal.</p>
        </div>
        <div className="profile">
          <span className="avatar">
            {displayName
              .split(/\s+/)
              .map((part) => part[0])
              .join("")
              .slice(0, 2)
              .toUpperCase()}
          </span>
          <span>
            <strong>{displayName}</strong>
            <small>{email}</small>
          </span>
          <a href="/signout-with-chatgpt?return_to=/" aria-label="Sign out">
            ↗
          </a>
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <button
            className="mobile-menu"
            onClick={() => setMenuOpen(!menuOpen)}
            aria-label="Toggle navigation"
          >
            ☰
          </button>
          <label className="search">
            <span>⌕</span>
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search forms…"
              aria-label="Search forms"
            />
            <kbd>⌘ K</kbd>
          </label>
          <div className="top-actions">
            <button className="icon-button" aria-label="Notifications">
              ♢<b></b>
            </button>
            <button className="primary" onClick={() => createForm()}>
              <span>＋</span>Create form
            </button>
          </div>
        </header>

        {loading ? (
          <Loading />
        ) : (
          <div className="content">
            {view === "dashboard" && (
              <Dashboard
                firstName={displayName.split(/\s+/)[0]}
                forms={forms}
                totalResponses={totalResponses}
                completion={completion}
                openEditor={openEditor}
                openResults={openResults}
                createForm={createForm}
                setView={setView}
              />
            )}
            {view === "forms" && (
              <FormsList
                forms={filtered}
                search={search}
                setSearch={setSearch}
                filter={filter}
                setFilter={setFilter}
                openEditor={openEditor}
                openResults={openResults}
                removeForm={removeForm}
                createForm={createForm}
              />
            )}
            {view === "templates" && <Templates createForm={createForm} />}
            {view === "editor" && draft && (
              <Editor
                draft={draft}
                setDraft={setDraft}
                updateQuestion={updateQuestion}
                moveQuestion={moveQuestion}
                saveDraft={saveDraft}
                saving={saving}
                setView={setView}
                setActiveId={setActiveId}
                copyPublicLink={copyPublicLink}
              />
            )}
            {view === "preview" && active && (
              <Responder
                form={active}
                answers={answers}
                setAnswers={setAnswers}
                submit={submitResponse}
                back={() => openEditor(active)}
              />
            )}
            {view === "results" && active && (
              <Results
                form={active}
                responses={responses}
                back={() => setView("forms")}
                edit={() => openEditor(active)}
                preview={() => openPublicForm(active)}
                copy={() => copyPublicLink(active)}
              />
            )}
          </div>
        )}
      </main>
      {notice && (
        <div className="toast" role="status">
          <span>✓</span>
          {notice}
        </div>
      )}
    </div>
  );
}

function Dashboard({
  firstName,
  forms,
  totalResponses,
  completion,
  openEditor,
  openResults,
  createForm,
  setView,
}: any) {
  const bars = [34, 52, 43, 69, 58, 78, 92];
  return (
    <>
      <section className="welcome">
        <div>
          <p className="eyebrow">Monday, July 13</p>
          <h1>
            Good morning, {firstName}
            <span>.</span>
          </h1>
          <p>Here’s how your forms are performing today.</p>
        </div>
        <button className="secondary" onClick={() => setView("templates")}>
          Browse templates <span>→</span>
        </button>
      </section>
      <section className="stats" aria-label="Workspace overview">
        <div className="stat-card">
          <span className="stat-icon indigo">▦</span>
          <p>Total forms</p>
          <strong>{forms.length}</strong>
          <small>
            <b>+2</b> this month
          </small>
        </div>
        <div className="stat-card">
          <span className="stat-icon cyan">↗</span>
          <p>Responses</p>
          <strong>{totalResponses.toLocaleString()}</strong>
          <small>
            <b>+18%</b> from last week
          </small>
        </div>
        <div className="stat-card">
          <span className="stat-icon green">◎</span>
          <p>Published</p>
          <strong>
            {forms.filter((f: FormRecord) => f.status === "published").length}
          </strong>
          <small>{completion}% of all forms</small>
        </div>
        <div className="trend-card">
          <div>
            <span>
              <p>Response trend</p>
              <strong>{Math.max(totalResponses, 24)}</strong>
            </span>
            <small>Last 7 days</small>
          </div>
          <div
            className="mini-chart"
            aria-label="Response trend over seven days"
          >
            {bars.map((height, index) => (
              <i
                key={index}
                style={{ height: `${height}%` }}
                className={index === bars.length - 1 ? "today" : ""}
              ></i>
            ))}
          </div>
          <div className="chart-days">
            <span>Mon</span>
            <span>Tue</span>
            <span>Wed</span>
            <span>Thu</span>
            <span>Fri</span>
            <span>Sat</span>
            <span>Sun</span>
          </div>
        </div>
      </section>
      <section className="section-head">
        <div>
          <h2>Recent forms</h2>
          <p>Pick up where you left off.</p>
        </div>
        <button className="text-button" onClick={() => setView("forms")}>
          View all <span>→</span>
        </button>
      </section>
      <div className="forms-table">
        <div className="table-head">
          <span>Form name</span>
          <span>Status</span>
          <span>Responses</span>
          <span>Last edited</span>
          <span></span>
        </div>
        {forms.slice(0, 4).map((form: FormRecord, index: number) => (
          <div
            className="form-row"
            key={form.id}
            onDoubleClick={() => openEditor(form)}
          >
            <span className={`form-thumb tone-${index % 3}`}>
              <i></i>
              <i></i>
              <i></i>
            </span>
            <span className="form-name">
              <strong>{form.title}</strong>
              <small>{form.questions.length} questions</small>
            </span>
            <span>
              <em className={`status ${form.status}`}>{form.status}</em>
            </span>
            <button className="row-link" onClick={() => openResults(form)}>
              {form.responseCount}
            </button>
            <span className="edited">{ago(form.updatedAt)}</span>
            <button
              className="row-menu"
              aria-label={`Edit ${form.title}`}
              onClick={() => openEditor(form)}
            >
              •••
            </button>
          </div>
        ))}
      </div>
      <button className="quick-create" onClick={() => createForm()}>
        <span>＋</span>
        <strong>Start from scratch</strong>
        <small>Create a blank form</small>
      </button>
    </>
  );
}

function FormsList({
  forms,
  search,
  setSearch,
  filter,
  setFilter,
  openEditor,
  openResults,
  removeForm,
  createForm,
}: any) {
  return (
    <>
      <section className="page-title">
        <div>
          <p className="eyebrow">Library</p>
          <h1>My forms</h1>
          <p>Create, organize and revisit every form in your workspace.</p>
        </div>
        <button className="primary" onClick={() => createForm()}>
          ＋ Create form
        </button>
      </section>
      <div className="list-toolbar">
        <label>
          <span>⌕</span>
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Find a form"
          />
        </label>
        <div className="segmented">
          {["all", "published", "draft"].map((item) => (
            <button
              key={item}
              onClick={() => setFilter(item)}
              className={filter === item ? "selected" : ""}
            >
              {item}
            </button>
          ))}
        </div>
      </div>
      <div className="form-grid">
        {forms.map((form: FormRecord, index: number) => (
          <article className="form-card" key={form.id}>
            <button
              className={`card-preview tone-${index % 3}`}
              onClick={() => openEditor(form)}
            >
              <span className="preview-pill"></span>
              <i></i>
              <i></i>
              <i></i>
            </button>
            <div className="card-body">
              <span>
                <em className={`status ${form.status}`}>{form.status}</em>
                <small>{form.questions.length} questions</small>
              </span>
              <h3>{form.title}</h3>
              <p>
                {form.description || "A new form waiting for your questions."}
              </p>
              <div>
                <button
                  className="secondary small"
                  onClick={() => openEditor(form)}
                >
                  Edit
                </button>
                <button
                  className="text-button small"
                  onClick={() => openResults(form)}
                >
                  {form.responseCount} responses
                </button>
                <button
                  className="danger-button"
                  onClick={() => removeForm(form)}
                  aria-label={`Delete ${form.title}`}
                >
                  ×
                </button>
              </div>
            </div>
          </article>
        ))}
        {forms.length === 0 && (
          <div className="empty">
            <span>⌕</span>
            <h3>No forms found</h3>
            <p>Try another search or start a new form.</p>
          </div>
        )}
      </div>
    </>
  );
}

function Templates({ createForm }: any) {
  const templateQuestions: Record<string, Question[]> = {
    "Customer survey": [
      {
        id: uid(),
        title: "How satisfied are you overall?",
        type: "rating",
        required: true,
      },
      {
        id: uid(),
        title: "What do you value most?",
        type: "long",
        required: false,
      },
      {
        id: uid(),
        title: "Would you recommend us?",
        type: "choice",
        required: true,
        options: ["Yes", "Maybe", "No"],
      },
    ],
    "Event registration": [
      { id: uid(), title: "Full name", type: "short", required: true },
      { id: uid(), title: "Email address", type: "email", required: true },
      {
        id: uid(),
        title: "Preferred session",
        type: "choice",
        required: true,
        options: ["Morning", "Afternoon"],
      },
    ],
    "Job application": [
      { id: uid(), title: "Full name", type: "short", required: true },
      { id: uid(), title: "Email address", type: "email", required: true },
      {
        id: uid(),
        title: "Why are you interested in this role?",
        type: "long",
        required: true,
      },
    ],
  };
  return (
    <>
      <section className="page-title">
        <div>
          <p className="eyebrow">Get a head start</p>
          <h1>Template gallery</h1>
          <p>Thoughtful starting points you can make your own.</p>
        </div>
      </section>
      <div className="template-feature">
        <div>
          <span>Featured template</span>
          <h2>Customer discovery</h2>
          <p>
            Learn what motivates your customers with a concise, research-ready
            survey.
          </p>
          <button
            className="light-button"
            onClick={() =>
              createForm(
                "Customer discovery",
                templateQuestions["Customer survey"],
              )
            }
          >
            Use this template →
          </button>
        </div>
        <div className="feature-paper">
          <span>Customer discovery</span>
          <i></i>
          <i></i>
          <i></i>
          <button>Continue</button>
        </div>
      </div>
      <div className="template-grid">
        {templates.map((template) => (
          <article key={template.title}>
            <div className={`template-art ${template.tone}`}>
              <span></span>
              <i></i>
              <i></i>
              <i></i>
            </div>
            <div>
              <small>{template.questions} questions</small>
              <h3>{template.title}</h3>
              <p>{template.description}</p>
              <button
                className="secondary small"
                onClick={() =>
                  createForm(template.title, templateQuestions[template.title])
                }
              >
                Use template
              </button>
            </div>
          </article>
        ))}
      </div>
    </>
  );
}

function Editor({
  draft,
  setDraft,
  updateQuestion,
  moveQuestion,
  saveDraft,
  saving,
  setView,
  setActiveId,
}: any) {
  const addQuestion = (type: QuestionType = "short") =>
    setDraft({
      ...draft,
      questions: [
        ...draft.questions,
        {
          id: uid(),
          title: "Untitled question",
          type,
          required: false,
          ...(type === "choice" ? { options: ["Option 1", "Option 2"] } : {}),
        },
      ],
    });
  return (
    <div className="editor-wrap">
      <section className="editor-bar">
        <button className="back-button" onClick={() => setView("forms")}>
          ←
        </button>
        <div>
          <small>Editing</small>
          <strong>{draft.title || "Untitled form"}</strong>
        </div>
        <span className="save-state">
          {saving ? "Saving…" : "Changes saved locally"}
        </span>
        <button
          className="secondary"
          onClick={() => {
            setActiveId(draft.id);
            setView("preview");
          }}
        >
          Preview
        </button>
        <button className="primary" onClick={() => saveDraft("published")}>
          {draft.status === "published" ? "Update" : "Publish"}
        </button>
      </section>
      <div className="editor-grid">
        <section className="builder">
          <div className="form-hero">
            <span className="accent-line"></span>
            <input
              className="title-input"
              value={draft.title}
              onChange={(e) => setDraft({ ...draft, title: e.target.value })}
              aria-label="Form title"
            />
            <textarea
              value={draft.description}
              onChange={(e) =>
                setDraft({ ...draft, description: e.target.value })
              }
              placeholder="Add a helpful introduction…"
              aria-label="Form description"
            />
          </div>
          {draft.questions.map((question: Question, index: number) => (
            <article className="question-card" key={question.id}>
              <div className="question-top">
                <span className="drag" aria-hidden="true">
                  ⠿
                </span>
                <span className="question-number">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <input
                  value={question.title}
                  onChange={(e) =>
                    updateQuestion(index, { title: e.target.value })
                  }
                  aria-label={`Question ${index + 1} title`}
                />
                <select
                  value={question.type}
                  onChange={(e) =>
                    updateQuestion(index, {
                      type: e.target.value as QuestionType,
                      ...(e.target.value === "choice" && !question.options
                        ? { options: ["Option 1", "Option 2"] }
                        : {}),
                    })
                  }
                  aria-label="Question type"
                >
                  {Object.entries(typeLabels).map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </select>
              </div>
              <QuestionPreview
                question={question}
                update={(patch) => updateQuestion(index, patch)}
              />
              <div className="question-actions">
                <button
                  onClick={() => moveQuestion(index, -1)}
                  disabled={index === 0}
                  aria-label="Move question up"
                >
                  ↑
                </button>
                <button
                  onClick={() => moveQuestion(index, 1)}
                  disabled={index === draft.questions.length - 1}
                  aria-label="Move question down"
                >
                  ↓
                </button>
                <span></span>
                <label>
                  Required{" "}
                  <input
                    type="checkbox"
                    checked={question.required}
                    onChange={(e) =>
                      updateQuestion(index, { required: e.target.checked })
                    }
                  />
                </label>
                <button
                  onClick={() =>
                    setDraft({
                      ...draft,
                      questions: draft.questions.filter(
                        (_: Question, i: number) => i !== index,
                      ),
                    })
                  }
                  aria-label="Delete question"
                >
                  ⌫
                </button>
              </div>
            </article>
          ))}
          <button className="add-question" onClick={() => addQuestion()}>
            ＋ Add question
          </button>
        </section>
        <aside className="editor-tools">
          <h3>Add question</h3>
          {Object.entries(typeLabels).map(([type, label]) => (
            <button
              key={type}
              onClick={() => addQuestion(type as QuestionType)}
            >
              <span>
                {type === "short"
                  ? "—"
                  : type === "long"
                    ? "☰"
                    : type === "email"
                      ? "@"
                      : type === "choice"
                        ? "◉"
                        : type === "rating"
                          ? "★"
                          : "▧"}
              </span>
              {label}
            </button>
          ))}
          <hr />
          <fieldset className="media-setting">
            <legend>Media upload</legend>
            <label>
              <input
                type="radio"
                name="media-mode"
                checked={draft.compressMedia !== false}
                onChange={() => setDraft({ ...draft, compressMedia: true })}
              />
              <span>
                <strong>Compress otomatis</strong>
                Gambar diperkecil sebelum dikirim
              </span>
            </label>
            <label>
              <input
                type="radio"
                name="media-mode"
                checked={draft.compressMedia === false}
                onChange={() => setDraft({ ...draft, compressMedia: false })}
              />
              <span>
                <strong>Simpan kualitas asli</strong>
                Unggah gambar tanpa perubahan
              </span>
            </label>
          </fieldset>
          <hr />
          <button onClick={() => saveDraft()} className="save-button">
            Save draft
          </button>
          <div className="editor-tip">
            <span>✦</span>
            <p>
              <strong>Keep it focused</strong>Forms with fewer than 10 questions
              have higher completion rates.
            </p>
          </div>
        </aside>
      </div>
    </div>
  );
}

function QuestionPreview({
  question,
  update,
}: {
  question: Question;
  update: (patch: Partial<Question>) => void;
}) {
  if (question.type === "choice")
    return (
      <div className="choice-editor">
        {(question.options ?? []).map((option, index) => (
          <label key={index}>
            <span>○</span>
            <input
              value={option}
              onChange={(e) => {
                const options = [...(question.options ?? [])];
                options[index] = e.target.value;
                update({ options });
              }}
            />
            <button
              onClick={() =>
                update({
                  options: question.options?.filter((_, i) => i !== index),
                })
              }
            >
              ×
            </button>
          </label>
        ))}
        <button
          onClick={() =>
            update({
              options: [
                ...(question.options ?? []),
                `Option ${(question.options?.length ?? 0) + 1}`,
              ],
            })
          }
        >
          ＋ Add option
        </button>
      </div>
    );
  if (question.type === "rating")
    return (
      <div className="rating-preview">
        {[1, 2, 3, 4, 5].map((n) => (
          <span key={n}>{n}</span>
        ))}
      </div>
    );
  if (question.type === "media")
    return (
      <div className="media-preview">
        <span>▧</span>
        <strong>Choose an image</strong>
        <small>JPG, PNG or WebP · up to 20 MB</small>
      </div>
    );
  return (
    <div className={`answer-line ${question.type === "long" ? "long" : ""}`}>
      {question.type === "email" ? "name@example.com" : "Respondent answer"}
    </div>
  );
}

function Responder({ form, answers, setAnswers, submit, back }: any) {
  return (
    <div className="responder">
      <button className="preview-back" onClick={back}>
        ← Back to editor
      </button>
      <div className="public-brand">
        <span className="brand-mark">
          <i></i>
          <i></i>
          <i></i>
        </span>
        forma
      </div>
      <form onSubmit={submit}>
        <div className="response-hero">
          <span>FORM</span>
          <h1>{form.title}</h1>
          <p>{form.description}</p>
          <small>
            <b>*</b> Required questions
          </small>
        </div>
        {form.questions.map((question: Question, index: number) => (
          <fieldset key={question.id}>
            <legend>
              <span>{index + 1}</span>
              {question.title}
              {question.required && <b>*</b>}
            </legend>
            {question.type === "media" ? (
              <div className="public-media-upload">
                <input type="file" accept="image/jpeg,image/png,image/webp" />
                <small>
                  {form.compressMedia
                    ? "Compress otomatis aktif"
                    : "Simpan kualitas asli"}
                </small>
              </div>
            ) : question.type === "long" ? (
              <textarea
                required={question.required}
                value={answers[question.id] || ""}
                onChange={(e) =>
                  setAnswers({ ...answers, [question.id]: e.target.value })
                }
                placeholder="Type your answer…"
              />
            ) : question.type === "choice" ? (
              <div className="public-choices">
                {question.options?.map((option) => (
                  <label key={option}>
                    <input
                      required={question.required}
                      type="radio"
                      name={question.id}
                      value={option}
                      checked={answers[question.id] === option}
                      onChange={(e) =>
                        setAnswers({
                          ...answers,
                          [question.id]: e.target.value,
                        })
                      }
                    />
                    <span>{option}</span>
                  </label>
                ))}
              </div>
            ) : question.type === "rating" ? (
              <div className="public-rating">
                {[1, 2, 3, 4, 5].map((value) => (
                  <label key={value}>
                    <input
                      required={question.required}
                      type="radio"
                      name={question.id}
                      value={value}
                      checked={answers[question.id] === String(value)}
                      onChange={(e) =>
                        setAnswers({
                          ...answers,
                          [question.id]: e.target.value,
                        })
                      }
                    />
                    <span>{value}</span>
                  </label>
                ))}
              </div>
            ) : (
              <input
                type={question.type === "email" ? "email" : "text"}
                required={question.required}
                value={answers[question.id] || ""}
                onChange={(e) =>
                  setAnswers({ ...answers, [question.id]: e.target.value })
                }
                placeholder="Type your answer…"
              />
            )}
          </fieldset>
        ))}
        <button className="submit-response" type="submit">
          Submit response <span>→</span>
        </button>
        <p className="privacy">
          Your answers are shared only with the form owner.
        </p>
      </form>
    </div>
  );
}

function Results({ form, responses, back, edit, preview }: any) {
  const bars = [
    22,
    38,
    31,
    58,
    49,
    68,
    Math.max(42, Math.min(92, 35 + responses.length * 7)),
  ];
  const firstChoice = form.questions.find((q: Question) => q.type === "choice");
  const counts = firstChoice
    ? (firstChoice.options ?? []).map((option: string) => ({
        option,
        count: responses.filter(
          (r: ResponseRecord) => r.answers[firstChoice.id] === option,
        ).length,
      }))
    : [];
  return (
    <>
      <section className="results-head">
        <button className="back-button" onClick={back}>
          ←
        </button>
        <div>
          <p className="eyebrow">Results</p>
          <h1>{form.title}</h1>
          <p>{form.responseCount} collected responses</p>
        </div>
        <button className="secondary" onClick={preview}>
          Open form
        </button>
        <button className="primary" onClick={edit}>
          Edit form
        </button>
      </section>
      <section className="result-stats">
        <div>
          <span>Total responses</span>
          <strong>{form.responseCount}</strong>
          <small>All time</small>
        </div>
        <div>
          <span>Completion rate</span>
          <strong>{form.responseCount ? "86%" : "—"}</strong>
          <small>Estimated from starts</small>
        </div>
        <div>
          <span>Average time</span>
          <strong>{form.responseCount ? "2:14" : "—"}</strong>
          <small>Minutes to complete</small>
        </div>
      </section>
      <div className="results-grid">
        <section className="response-chart">
          <div>
            <h2>Responses over time</h2>
            <select aria-label="Chart range">
              <option>Last 7 days</option>
              <option>Last 30 days</option>
            </select>
          </div>
          <div className="large-chart">
            {bars.map((height, index) => (
              <span key={index}>
                <i style={{ height: `${height}%` }}></i>
                <small>
                  {["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][index]}
                </small>
              </span>
            ))}
          </div>
        </section>
        <section className="choice-summary">
          <h2>{firstChoice?.title ?? "Response activity"}</h2>
          {counts.length ? (
            counts.map((item: any, index: number) => (
              <div key={item.option}>
                <span>
                  <i className={`dot dot-${index}`}></i>
                  {item.option}
                  <b>{item.count}</b>
                </span>
                <em>
                  <i
                    style={{
                      width: `${responses.length ? Math.max(6, (item.count / responses.length) * 100) : 0}%`,
                    }}
                  ></i>
                </em>
              </div>
            ))
          ) : (
            <div className="no-responses">
              <span>◎</span>
              <p>Choice summaries appear here as responses arrive.</p>
            </div>
          )}
        </section>
      </div>
      <section className="responses-section">
        <div className="section-head">
          <div>
            <h2>Individual responses</h2>
            <p>Most recent submissions first.</p>
          </div>
        </div>
        {responses.length ? (
          <div className="response-table">
            <div className="response-row head">
              <span>Submitted</span>
              {form.questions.slice(0, 3).map((q: Question) => (
                <span key={q.id}>{q.title}</span>
              ))}
            </div>
            {responses.map((response: ResponseRecord) => (
              <div className="response-row" key={response.id}>
                <span>
                  {new Date(response.submittedAt).toLocaleDateString()}
                </span>
                {form.questions.slice(0, 3).map((q: Question) => (
                  <span key={q.id}>
                    {response.answers[q.id]?.startsWith("/api/media/") ? (
                      <a
                        href={response.answers[q.id]}
                        target="_blank"
                        rel="noreferrer"
                      >
                        Lihat media ↗
                      </a>
                    ) : (
                      response.answers[q.id] || "—"
                    )}
                  </span>
                ))}
              </div>
            ))}
          </div>
        ) : (
          <div className="empty-results">
            <span>↗</span>
            <h3>No responses yet</h3>
            <p>
              Open the form and submit a response to see it appear here
              instantly.
            </p>
            <button className="primary" onClick={preview}>
              Open form
            </button>
          </div>
        )}
      </section>
    </>
  );
}

function Loading() {
  return (
    <div className="loading">
      <span></span>
      <i></i>
      <i></i>
      <i></i>
    </div>
  );
}
