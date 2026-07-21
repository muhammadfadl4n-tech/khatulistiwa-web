import { db, ensureDatabase } from "@/db/store";
import { getChatGPTUser } from "../../chatgpt-auth";

type Question = {
  id: string;
  title: string;
  type: string;
  required: boolean;
  options?: string[];
};

const starterForms = [
  {
    id: "customer-feedback",
    title: "Customer feedback",
    description: "Help us understand what is working and where we can improve.",
    status: "published",
    questions: [
      {
        id: "rating",
        title: "How would you rate your experience?",
        type: "rating",
        required: true,
      },
      {
        id: "favorite",
        title: "What did you enjoy most?",
        type: "long",
        required: false,
      },
      {
        id: "recommend",
        title: "Would you recommend us?",
        type: "choice",
        required: true,
        options: ["Definitely", "Maybe", "Not yet"],
      },
    ],
    createdAt: Date.now() - 1000 * 60 * 60 * 24 * 18,
    updatedAt: Date.now() - 1000 * 60 * 28,
  },
  {
    id: "event-registration",
    title: "Event registration",
    description: "Reserve your place for our next community gathering.",
    status: "published",
    questions: [
      { id: "name", title: "Full name", type: "short", required: true },
      { id: "email", title: "Email address", type: "email", required: true },
      {
        id: "session",
        title: "Preferred session",
        type: "choice",
        required: true,
        options: ["Morning", "Afternoon", "Evening"],
      },
    ],
    createdAt: Date.now() - 1000 * 60 * 60 * 24 * 9,
    updatedAt: Date.now() - 1000 * 60 * 60 * 5,
  },
  {
    id: "team-pulse",
    title: "Team pulse",
    description: "A quick weekly check-in for the product team.",
    status: "draft",
    questions: [
      {
        id: "mood",
        title: "How are you feeling this week?",
        type: "choice",
        required: true,
        options: ["Energized", "Steady", "Stretched"],
      },
      {
        id: "support",
        title: "What support would help most?",
        type: "long",
        required: false,
      },
    ],
    createdAt: Date.now() - 1000 * 60 * 60 * 24 * 3,
    updatedAt: Date.now() - 1000 * 60 * 60 * 22,
  },
];

async function seed() {
  const database = db();
  const count = await database
    .prepare("SELECT COUNT(*) AS count FROM forms")
    .first<{ count: number }>();
  if ((count?.count ?? 0) > 0) return;
  await database.batch(
    starterForms.map((form) =>
      database
        .prepare(
          "INSERT INTO forms (id,title,description,status,questions,created_at,updated_at) VALUES (?,?,?,?,?,?,?)",
        )
        .bind(
          form.id,
          form.title,
          form.description,
          form.status,
          JSON.stringify(form.questions),
          form.createdAt,
          form.updatedAt,
        ),
    ),
  );
}

export async function GET() {
  const user = await getChatGPTUser();
  if (!user) return Response.json({ error: "Unauthorized" }, { status: 401 });
  await ensureDatabase();
  await seed();
  const database = db();
  await database
    .prepare(
      "UPDATE forms SET owner_email=? WHERE owner_email IS NULL OR owner_email=''",
    )
    .bind(user.email)
    .run();
  const result = await database
    .prepare(
      `SELECT f.*, COUNT(r.id) AS response_count
    FROM forms f LEFT JOIN responses r ON r.form_id = f.id
    WHERE f.owner_email=? GROUP BY f.id ORDER BY f.updated_at DESC`,
    )
    .bind(user.email)
    .all();
  const results = (result.results ?? []) as Array<{
    id: string;
    title: string;
    description: string;
    status: string;
    questions: string;
    created_at: number;
    updated_at: number;
    response_count: number;
    compress_media: number;
  }>;
  const forms = results.map((row) => ({
    id: row.id,
    title: row.title,
    description: row.description,
    status: row.status,
    questions: JSON.parse(row.questions),
    createdAt: row.created_at,
    updatedAt: row.updated_at,
    responseCount: Number(row.response_count || 0),
    compressMedia: Boolean(row.compress_media),
  }));
  return Response.json({ forms });
}

export async function POST(request: Request) {
  const user = await getChatGPTUser();
  if (!user) return Response.json({ error: "Unauthorized" }, { status: 401 });
  await ensureDatabase();
  const body = (await request.json()) as Partial<{
    title: string;
    description: string;
    questions: Question[];
    compressMedia: boolean;
  }>;
  const id = crypto.randomUUID();
  const now = Date.now();
  const questions = body.questions ?? [
    {
      id: crypto.randomUUID(),
      title: "Untitled question",
      type: "short",
      required: false,
    },
  ];
  await db()
    .prepare(
      "INSERT INTO forms (id,title,description,status,questions,owner_email,compress_media,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?)",
    )
    .bind(
      id,
      body.title || "Untitled form",
      body.description || "",
      "draft",
      JSON.stringify(questions),
      user.email,
      body.compressMedia === false ? 0 : 1,
      now,
      now,
    )
    .run();
  return Response.json({ id }, { status: 201 });
}

export async function PATCH(request: Request) {
  const user = await getChatGPTUser();
  if (!user) return Response.json({ error: "Unauthorized" }, { status: 401 });
  await ensureDatabase();
  const body = (await request.json()) as {
    id: string;
    title: string;
    description: string;
    status: string;
    questions: Question[];
    compressMedia: boolean;
  };
  await db()
    .prepare(
      "UPDATE forms SET title=?, description=?, status=?, questions=?, compress_media=?, updated_at=? WHERE id=? AND owner_email=?",
    )
    .bind(
      body.title,
      body.description,
      body.status,
      JSON.stringify(body.questions),
      body.compressMedia === false ? 0 : 1,
      Date.now(),
      body.id,
      user.email,
    )
    .run();
  return Response.json({ ok: true });
}

export async function DELETE(request: Request) {
  const user = await getChatGPTUser();
  if (!user) return Response.json({ error: "Unauthorized" }, { status: 401 });
  await ensureDatabase();
  const id = new URL(request.url).searchParams.get("id");
  if (!id) return Response.json({ error: "Missing form id" }, { status: 400 });
  const database = db();
  const owned = await database
    .prepare("SELECT id FROM forms WHERE id=? AND owner_email=?")
    .bind(id, user.email)
    .first();
  if (!owned) return Response.json({ error: "Not found" }, { status: 404 });
  await database.batch([
    database.prepare("DELETE FROM responses WHERE form_id=?").bind(id),
    database
      .prepare("DELETE FROM forms WHERE id=? AND owner_email=?")
      .bind(id, user.email),
  ]);
  return Response.json({ ok: true });
}
