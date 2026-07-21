import { db, ensureDatabase } from "@/db/store";
import { getChatGPTUser } from "../../chatgpt-auth";

export async function GET(request: Request) {
  const user = await getChatGPTUser();
  if (!user) return Response.json({ error: "Unauthorized" }, { status: 401 });
  await ensureDatabase();
  const formId = new URL(request.url).searchParams.get("formId");
  if (!formId) return Response.json({ responses: [] });
  const result = await db()
    .prepare(
      "SELECT r.* FROM responses r JOIN forms f ON f.id=r.form_id WHERE r.form_id=? AND f.owner_email=? ORDER BY r.submitted_at DESC",
    )
    .bind(formId, user.email)
    .all();
  const rows = (result.results ?? []) as Array<{
    id: string;
    answers: string;
    submitted_at: number;
  }>;
  return Response.json({
    responses: rows.map((row) => ({
      id: row.id,
      answers: JSON.parse(row.answers),
      submittedAt: row.submitted_at,
    })),
  });
}

export async function POST(request: Request) {
  await ensureDatabase();
  const body = (await request.json()) as {
    formId: string;
    answers: Record<string, string>;
  };
  const published = await db()
    .prepare("SELECT id FROM forms WHERE id=? AND status='published'")
    .bind(body.formId)
    .first();
  if (!published)
    return Response.json({ error: "Form not found" }, { status: 404 });
  const id = crypto.randomUUID();
  await db()
    .prepare(
      "INSERT INTO responses (id,form_id,answers,submitted_at) VALUES (?,?,?,?)",
    )
    .bind(id, body.formId, JSON.stringify(body.answers), Date.now())
    .run();
  return Response.json({ id }, { status: 201 });
}
