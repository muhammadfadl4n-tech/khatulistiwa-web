import { integer, sqliteTable, text } from "drizzle-orm/sqlite-core";

export const forms = sqliteTable("forms", {
  id: text("id").primaryKey(),
  title: text("title").notNull(),
  description: text("description").notNull().default(""),
  status: text("status").notNull().default("draft"),
  questions: text("questions").notNull().default("[]"),
  ownerEmail: text("owner_email"),
  compressMedia: integer("compress_media").notNull().default(1),
  createdAt: integer("created_at").notNull(),
  updatedAt: integer("updated_at").notNull(),
});

export const responses = sqliteTable("responses", {
  id: text("id").primaryKey(),
  formId: text("form_id").notNull(),
  answers: text("answers").notNull().default("{}"),
  submittedAt: integer("submitted_at").notNull(),
});
