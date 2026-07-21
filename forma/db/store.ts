import { env } from "cloudflare:workers";

type D1 = {
  prepare(sql: string): {
    bind(...values: unknown[]): any;
    run(): Promise<any>;
    all<T>(): Promise<{ results?: T[] }>;
    first<T>(): Promise<T | null>;
  };
  batch(statements: any[]): Promise<any[]>;
};

export function db(): D1 {
  const database = (env as unknown as { DB?: D1 }).DB;
  if (!database) throw new Error("Database binding is unavailable");
  return database;
}

export async function ensureDatabase() {
  const database = db();
  await database.batch([
    database.prepare(`CREATE TABLE IF NOT EXISTS forms (
      id TEXT PRIMARY KEY,
      title TEXT NOT NULL,
      description TEXT NOT NULL DEFAULT '',
      status TEXT NOT NULL DEFAULT 'draft',
      questions TEXT NOT NULL DEFAULT '[]',
      owner_email TEXT,
      compress_media INTEGER NOT NULL DEFAULT 1,
      created_at INTEGER NOT NULL,
      updated_at INTEGER NOT NULL
    )`),
    database.prepare(`CREATE TABLE IF NOT EXISTS responses (
      id TEXT PRIMARY KEY,
      form_id TEXT NOT NULL,
      answers TEXT NOT NULL DEFAULT '{}',
      submitted_at INTEGER NOT NULL
    )`),
    database.prepare(
      "CREATE INDEX IF NOT EXISTS responses_form_id_idx ON responses (form_id)",
    ),
  ]);
  const columns = await database
    .prepare("PRAGMA table_info(forms)")
    .all<{ name: string }>();
  if (
    !(columns.results ?? []).some((column) => column.name === "owner_email")
  ) {
    await database
      .prepare("ALTER TABLE forms ADD COLUMN owner_email TEXT")
      .run();
  }
  if (
    !(columns.results ?? []).some((column) => column.name === "compress_media")
  ) {
    await database
      .prepare(
        "ALTER TABLE forms ADD COLUMN compress_media INTEGER NOT NULL DEFAULT 1",
      )
      .run();
  }
}

export function mediaBucket(): R2Bucket {
  const bucket = (env as unknown as { MEDIA?: R2Bucket }).MEDIA;
  if (!bucket) throw new Error("Media storage binding is unavailable");
  return bucket;
}
