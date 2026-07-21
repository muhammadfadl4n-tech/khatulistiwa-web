import { notFound } from "next/navigation";
import { db, ensureDatabase } from "@/db/store";
import PublicForm from "./PublicForm";

export const dynamic = "force-dynamic";

export default async function PublicFormPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  await ensureDatabase();
  const row = (await db()
    .prepare(
      "SELECT id,title,description,status,questions,compress_media FROM forms WHERE id=?",
    )
    .bind(id)
    .first()) as null | {
    id: string;
    title: string;
    description: string;
    status: string;
    questions: string;
    compress_media: number;
  };
  if (!row || row.status !== "published") notFound();
  return (
    <PublicForm
      form={{
        ...row,
        compressMedia: Boolean(row.compress_media),
        questions: JSON.parse(row.questions),
      }}
    />
  );
}
