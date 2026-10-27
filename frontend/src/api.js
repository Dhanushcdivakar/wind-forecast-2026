const API_URL = import.meta.env.VITE_API_URL ?? (import.meta.env.PROD ? "" : "http://localhost:8000");
async function get(path) {
  const response = await fetch(`${API_URL}${path}`);
  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try { const body = await response.json(); if (body.detail) message = body.detail; } catch {}
    throw new Error(message);
  }
  return response.json();
}
export const getOverview = () => get("/api/overview");
export const getGeneration = () => get("/api/generation");
export const getAccuracy = () => get("/api/accuracy");
export const getHistory = (date) => get(`/api/forecast-history${date ? `?target_date=${encodeURIComponent(date)}` : ""}`);
export const getData = (date) => get(`/api/data${date ? `?target_date=${encodeURIComponent(date)}` : ""}`);
