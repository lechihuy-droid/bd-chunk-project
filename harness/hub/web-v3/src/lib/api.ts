export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) { super(message); this.status = status }
}

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await apiRequest(path, init)
  return response.json() as Promise<T>
}

export async function apiRequest(path: string, init: RequestInit = {}): Promise<Response> {
  const headers = new Headers(init.headers)
  if (init.method && init.method !== 'GET') headers.set('X-Hub-Client', 'harness-hub')
  if (init.body && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json')
  const response = await fetch(path, { ...init, headers })
  if (!response.ok) {
    let message = `Request failed (${response.status})`
    try { const body = await response.json() as { detail?: string; message?: string }; message = body.detail ?? body.message ?? message } catch { /* plain error response */ }
    throw new ApiError(response.status, message)
  }
  return response
}
