import { useCallback, useEffect, useMemo, useState } from "react";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

export function useSalons(filters) {
  const [salons, setSalons] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const query = useMemo(() => {
    const params = new URLSearchParams();
    if (filters.district) params.set("district", filters.district);
    if (filters.service) params.set("service", filters.service);
    if (filters.q) params.set("q", filters.q);
    if (filters.sort_by) params.set("sort_by", filters.sort_by);
    return params.toString();
  }, [filters]);

  const fetchSalons = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/salons${query ? `?${query}` : ""}`);
      if (!response.ok) throw new Error("Failed to load salons");
      setSalons(await response.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }, [query]);

  useEffect(() => {
    fetchSalons();
  }, [fetchSalons]);

  return { salons, loading, error, refetch: fetchSalons };
}

export async function fetchSalon(id) {
  const response = await fetch(`${API_BASE_URL}/salons/${id}`);
  if (!response.ok) throw new Error("Failed to load salon details");
  return response.json();
}

export async function updateSalon(id, payload) {
  const response = await fetch(`${API_BASE_URL}/salons/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error("Failed to update salon");
  return response.json();
}

export async function refreshScraper(salonCount) {
  const params = new URLSearchParams({ source: "booksy", salon_count: String(salonCount) });
  const response = await fetch(`${API_BASE_URL}/scraper/run?${params.toString()}`, { method: "POST" });
  if (!response.ok) throw new Error("Failed to start scraper");
  return response.json();
}

export async function fetchScraperStatus() {
  const response = await fetch(`${API_BASE_URL}/scraper/status`);
  if (!response.ok) throw new Error("Failed to load scraper status");
  return response.json();
}
