import { createHash } from "node:crypto";
import { mkdir, readFile, stat, writeFile } from "node:fs/promises";
import { createRequire } from "node:module";
import path from "node:path";
import type DatabaseTypes from "better-sqlite3";

const require = createRequire(import.meta.url);
const Database = require("better-sqlite3") as typeof DatabaseTypes;

const dataDirectory = process.env.DATA_DIR || path.join(process.cwd(), "data");
const mediaDirectory = path.join(dataDirectory, "media");
let database: DatabaseTypes.Database | null = null;

class NodeStatement {
  private values: unknown[] = [];

  constructor(
    private readonly connection: DatabaseTypes.Database,
    private readonly sql: string,
  ) {}

  bind(...values: unknown[]) {
    this.values = values;
    return this;
  }

  async run() {
    return this.connection.prepare(this.sql).run(...this.values);
  }

  async all<T>() {
    return {
      results: this.connection.prepare(this.sql).all(...this.values) as T[],
    };
  }

  async first<T>() {
    return (this.connection.prepare(this.sql).get(...this.values) as T) ?? null;
  }

  executeSync() {
    return this.connection.prepare(this.sql).run(...this.values);
  }
}

function connection() {
  if (!database) {
    database = new Database(path.join(dataDirectory, "forma.sqlite"));
    database.pragma("journal_mode = WAL");
    database.pragma("foreign_keys = ON");
  }
  return database;
}

export function db() {
  const current = connection();
  return {
    prepare(sql: string) {
      return new NodeStatement(current, sql);
    },
    async batch(statements: NodeStatement[]) {
      return current.transaction(() =>
        statements.map((statement) => statement.executeSync()),
      )();
    },
  };
}

export async function ensureDatabase() {
  await mkdir(mediaDirectory, { recursive: true });
  const current = db();
  await current.batch([
    current.prepare(`CREATE TABLE IF NOT EXISTS forms (
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
    current.prepare(`CREATE TABLE IF NOT EXISTS responses (
      id TEXT PRIMARY KEY,
      form_id TEXT NOT NULL,
      answers TEXT NOT NULL DEFAULT '{}',
      submitted_at INTEGER NOT NULL
    )`),
    current.prepare(
      "CREATE INDEX IF NOT EXISTS responses_form_id_idx ON responses (form_id)",
    ),
  ]);
}

function safeMediaKey(value: string) {
  if (!/^[a-f0-9-]{36}$/i.test(value)) throw new Error("Invalid media key");
  return value;
}

export function mediaBucket() {
  return {
    async put(
      rawKey: string,
      body: ReadableStream<Uint8Array>,
      options?: {
        httpMetadata?: { contentType?: string; cacheControl?: string };
        customMetadata?: Record<string, string>;
      },
    ) {
      await mkdir(mediaDirectory, { recursive: true });
      const key = safeMediaKey(rawKey);
      const bytes = new Uint8Array(await new Response(body).arrayBuffer());
      await writeFile(path.join(mediaDirectory, key), bytes);
      await writeFile(
        path.join(mediaDirectory, `${key}.json`),
        JSON.stringify(options ?? {}),
        "utf8",
      );
    },
    async get(rawKey: string) {
      try {
        const key = safeMediaKey(rawKey);
        const [bytes, details, fileStats] = await Promise.all([
          readFile(path.join(mediaDirectory, key)),
          readFile(path.join(mediaDirectory, `${key}.json`), "utf8").then(
            (value) => JSON.parse(value) as {
              httpMetadata?: { contentType?: string; cacheControl?: string };
            },
          ),
          stat(path.join(mediaDirectory, key)),
        ]);
        return {
          body: new Uint8Array(bytes),
          httpEtag: `"${createHash("sha256").update(bytes).digest("hex")}"`,
          writeHttpMetadata(headers: Headers) {
            if (details.httpMetadata?.contentType)
              headers.set("content-type", details.httpMetadata.contentType);
            if (details.httpMetadata?.cacheControl)
              headers.set("cache-control", details.httpMetadata.cacheControl);
            headers.set("content-length", String(fileStats.size));
          },
        };
      } catch {
        return null;
      }
    },
  };
}
