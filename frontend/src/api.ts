import axios from "axios";
import type { Prediction, ModelInfo, Category, HistoryData } from "./types";
const client = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "",
  timeout: 30000,
});
export const api = {
  health: () =>
    client
      .get<{ model_ready: boolean; history_enabled: boolean }>("/api/health")
      .then((r) => r.data),
  info: () => client.get<ModelInfo>("/api/model-info").then((r) => r.data),
  categories: () =>
    client.get<Category[]>("/api/categories").then((r) => r.data),
  predict: (code: string, language: string) =>
    client
      .post<Prediction>("/api/predict", { code, language })
      .then((r) => r.data),
  history: () => client.get<HistoryData>("/api/history").then((r) => r.data),
  deleteScan: (id: number) => client.delete(`/api/history/${id}`),
};
export function errorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    if (error.code === "ECONNABORTED")
      return "The analysis timed out. Please try again.";
    const detail = error.response?.data?.detail;
    return typeof detail === "string"
      ? detail
      : Array.isArray(detail)
        ? detail.map((d) => d.message).join(". ")
        : "Cannot reach the backend. Check that the API is running.";
  }
  return error instanceof Error
    ? error.message
    : "Something went wrong. Please try again.";
}
