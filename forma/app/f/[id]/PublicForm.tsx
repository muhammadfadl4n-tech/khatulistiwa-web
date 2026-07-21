"use client";

import { useState } from "react";

type Question = {
  id: string;
  title: string;
  type: "short" | "long" | "email" | "choice" | "rating" | "media";
  required: boolean;
  options?: string[];
};
type PublicFormRecord = {
  id: string;
  title: string;
  description: string;
  status: string;
  questions: Question[];
  compressMedia: boolean;
};

async function compressImage(file: File): Promise<File> {
  if (!file.type.startsWith("image/") || file.size < 350_000) return file;
  const bitmap = await createImageBitmap(file);
  const scale = Math.min(1, 1600 / Math.max(bitmap.width, bitmap.height));
  const canvas = document.createElement("canvas");
  canvas.width = Math.max(1, Math.round(bitmap.width * scale));
  canvas.height = Math.max(1, Math.round(bitmap.height * scale));
  canvas.getContext("2d")?.drawImage(bitmap, 0, 0, canvas.width, canvas.height);
  bitmap.close();
  const blob = await new Promise<Blob | null>((resolve) =>
    canvas.toBlob(resolve, "image/webp", 0.78),
  );
  if (!blob || blob.size >= file.size) return file;
  return new File([blob], file.name.replace(/\.[^.]+$/, "") + ".webp", {
    type: "image/webp",
  });
}

export default function PublicForm({ form }: { form: PublicFormRecord }) {
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [submitted, setSubmitted] = useState(false);
  const [sending, setSending] = useState(false);
  const [files, setFiles] = useState<Record<string, File>>({});
  const [error, setError] = useState("");

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setSending(true);
    setError("");
    const finalAnswers = { ...answers };
    for (const question of form.questions.filter(
      (item) => item.type === "media",
    )) {
      const selected = files[question.id];
      if (!selected) continue;
      const file = form.compressMedia
        ? await compressImage(selected)
        : selected;
      const upload = new FormData();
      upload.set("formId", form.id);
      upload.set("questionId", question.id);
      upload.set("file", file);
      const mediaResponse = await fetch("/api/media", {
        method: "POST",
        body: upload,
      });
      const mediaResult = (await mediaResponse.json()) as {
        url?: string;
        error?: string;
      };
      if (!mediaResponse.ok || !mediaResult.url) {
        setError(mediaResult.error || "Media gagal diunggah");
        setSending(false);
        return;
      }
      finalAnswers[question.id] = mediaResult.url;
    }
    const response = await fetch("/api/responses", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ formId: form.id, answers: finalAnswers }),
    });
    setSending(false);
    if (response.ok) setSubmitted(true);
  }

  if (submitted)
    return (
      <main className="public-page">
        <div className="public-brand">
          <span className="brand-mark">
            <i></i>
            <i></i>
            <i></i>
          </span>
          forma
        </div>
        <section className="thank-you">
          <span>✓</span>
          <h1>Response recorded</h1>
          <p>
            Thank you for completing “{form.title}”. Your answer has been sent
            to the form owner.
          </p>
          <button
            onClick={() => {
              setAnswers({});
              setFiles({});
              setSubmitted(false);
            }}
          >
            Submit another response
          </button>
        </section>
      </main>
    );

  return (
    <main className="public-page">
      <div className="public-brand">
        <span className="brand-mark">
          <i></i>
          <i></i>
          <i></i>
        </span>
        forma
      </div>
      <form className="public-form" onSubmit={submit}>
        <div className="response-hero">
          <span>FORM</span>
          <h1>{form.title}</h1>
          <p>{form.description}</p>
          <small>
            <b>*</b> Required questions
          </small>
        </div>
        {form.questions.map((question, index) => (
          <fieldset key={question.id}>
            <legend>
              <span>{index + 1}</span>
              {question.title}
              {question.required && <b>*</b>}
            </legend>
            {question.type === "media" ? (
              <div className="public-media-upload">
                <input
                  type="file"
                  accept="image/jpeg,image/png,image/webp"
                  required={question.required}
                  onChange={(event) => {
                    const file = event.target.files?.[0];
                    if (file) setFiles({ ...files, [question.id]: file });
                  }}
                />
                <small>
                  {form.compressMedia
                    ? "Compress otomatis aktif · maksimal 20 MB"
                    : "Kualitas asli · maksimal 20 MB"}
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
        <button className="submit-response" type="submit" disabled={sending}>
          {sending ? "Sending…" : "Submit response"}
          <span>→</span>
        </button>
        {error && <p className="upload-error">{error}</p>}
        <p className="privacy">
          Your answers are shared only with the form owner. No ChatGPT login is
          required.
        </p>
      </form>
    </main>
  );
}
