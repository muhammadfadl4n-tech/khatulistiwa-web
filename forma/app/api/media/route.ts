import { db, ensureDatabase, mediaBucket } from "@/db/store";

const MAX_MEDIA_BYTES = 20 * 1024 * 1024;

export async function POST(request: Request) {
  await ensureDatabase();
  const data = await request.formData();
  const formId = String(data.get("formId") ?? "");
  const questionId = String(data.get("questionId") ?? "");
  const file = data.get("file");
  if (!(file instanceof File) || !formId || !questionId) {
    return Response.json({ error: "Upload tidak lengkap" }, { status: 400 });
  }
  if (!file.type.startsWith("image/")) {
    return Response.json(
      { error: "Saat ini hanya gambar yang didukung" },
      { status: 415 },
    );
  }
  if (file.size > MAX_MEDIA_BYTES) {
    return Response.json(
      { error: "Ukuran gambar maksimal 20 MB" },
      { status: 413 },
    );
  }
  const row = (await db()
    .prepare("SELECT questions FROM forms WHERE id=? AND status='published'")
    .bind(formId)
    .first()) as { questions: string } | null;
  const questions = row
    ? (JSON.parse(row.questions) as Array<{ id: string; type: string }>)
    : [];
  if (
    !questions.some(
      (question) => question.id === questionId && question.type === "media",
    )
  ) {
    return Response.json(
      { error: "Pertanyaan upload tidak ditemukan" },
      { status: 404 },
    );
  }
  const key = crypto.randomUUID();
  await mediaBucket().put(key, file.stream(), {
    httpMetadata: {
      contentType: file.type,
      cacheControl: "public, max-age=31536000, immutable",
    },
    customMetadata: {
      formId,
      questionId,
      originalName: file.name.slice(0, 120),
    },
  });
  return Response.json({
    url: `/api/media/${key}`,
    name: file.name,
    size: file.size,
  });
}
