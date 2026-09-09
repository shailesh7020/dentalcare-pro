import axios from "axios";

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export const api = axios.create({ baseURL: apiUrl, timeout: 10_000 });

let accessToken: string | null = null;
let onUnauthorized: (() => Promise<void>) | null = null;

export function configureApiSession(token: string | null, unauthorized: () => Promise<void>): void {
  accessToken = token;
  onUnauthorized = unauthorized;
}

api.interceptors.request.use((config) => {
  if (accessToken) config.headers.Authorization = `Bearer ${accessToken}`;
  return config;
});
api.interceptors.response.use(undefined, async (error) => {
  if (error.response?.status === 401 && onUnauthorized) await onUnauthorized();
  return Promise.reject(error);
});

export async function refreshAccessToken(): Promise<string> {
  const response = await fetch("/api/auth/refresh", { method: "POST", credentials: "same-origin" });
  if (!response.ok) throw new Error("Session expired");
  return (await response.json()).access_token as string;
}
