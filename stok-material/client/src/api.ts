type QueryParams = Record<string, string | number | boolean | null | undefined>

const baseUrl = ""

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${baseUrl}${path}`, {
    ...options,
    credentials: "include",
    headers: {
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      ...options.headers,
    },
  })

  const contentType = response.headers.get("content-type") ?? ""
  const data = contentType.includes("application/json") ? await response.json() : await response.text()

  if (!response.ok) {
    const message =
      typeof data === "object" && data !== null && "message" in data
        ? String(data.message)
        : typeof data === "object" && data !== null && "error" in data
          ? String(data.error)
          : `Request failed with status ${response.status}`
    throw new Error(message)
  }

  return data as T
}

function withParams(path: string, params?: QueryParams) {
  if (!params) return path

  const query = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      query.set(key, String(value))
    }
  })

  const serialized = query.toString()
  return serialized ? `${path}?${serialized}` : path
}

export const api = {
  get: <T>(path: string, params?: QueryParams) => request<T>(withParams(path, params), { method: "GET" }),
  post: <T>(path: string, body: unknown) => request<T>(path, { method: "POST", body: JSON.stringify(body) }),
  put: <T>(path: string, body: unknown) => request<T>(path, { method: "PUT", body: JSON.stringify(body) }),
  del: <T>(path: string) => request<T>(path, { method: "DELETE" }),
}
