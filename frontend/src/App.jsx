import { RefreshCw } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { Filters } from "./components/Filters";
import { SalonCard } from "./components/SalonCard";
import { SalonDetails } from "./components/SalonDetails";
import {
  enrichSalonDetails,
  fetchDistricts,
  fetchDetailEnrichmentStatus,
  fetchScraperStatus,
  refreshScraper,
  useSalons,
} from "./hooks/useSalons";

export default function App() {
  const [filters, setFilters] = useState({
    q: "",
    district: "",
    service: "",
    sort_by: "reviews_count",
    sort_order: "desc",
  });
  const [selectedSalonId, setSelectedSalonId] = useState(null);
  const [refreshStatus, setRefreshStatus] = useState("");
  const [salonCount, setSalonCount] = useState(100);
  const [scraperStatus, setScraperStatus] = useState(null);
  const [detailStatus, setDetailStatus] = useState(null);
  const [districts, setDistricts] = useState([]);
  const { salons, loading, error, refetch } = useSalons(filters);
  const pagesToScrape = Math.ceil(Number(salonCount || 0) / 20);

  const loadDistricts = useCallback(async () => {
    try {
      setDistricts(await fetchDistricts());
    } catch (error) {
      setRefreshStatus(error.message);
    }
  }, []);

  const startRefresh = async () => {
    setRefreshStatus("Starting scraper...");
    try {
      const status = await refreshScraper(salonCount);
      setScraperStatus(status);
      setRefreshStatus("Scraper started");
    } catch (error) {
      setRefreshStatus(error.message);
    }
  };

  const startDetailParsing = async () => {
    setRefreshStatus("Starting detail parsing...");
    try {
      const status = await enrichSalonDetails(salonCount);
      setDetailStatus(status);
      setRefreshStatus("Detail parsing started");
    } catch (error) {
      setRefreshStatus(error.message);
    }
  };

  useEffect(() => {
    loadDistricts();
  }, [loadDistricts]);

  useEffect(() => {
    if (scraperStatus?.status !== "running") return undefined;

    const intervalId = window.setInterval(async () => {
      try {
        const status = await fetchScraperStatus();
        setScraperStatus(status);
        if (status.status === "finished") {
          setRefreshStatus(`Finished: ${status.parsed_count} parsed`);
          refetch();
          loadDistricts();
        }
        if (status.status === "failed") {
          setRefreshStatus(status.error || "Scraper failed");
        }
      } catch (error) {
        setRefreshStatus(error.message);
      }
    }, 1000);

    return () => window.clearInterval(intervalId);
  }, [scraperStatus?.status, refetch, loadDistricts]);

  useEffect(() => {
    if (detailStatus?.status !== "running") return undefined;

    const intervalId = window.setInterval(async () => {
      try {
        const status = await fetchDetailEnrichmentStatus();
        setDetailStatus(status);
        if (status.status === "finished") {
          setRefreshStatus(`Details parsed: ${status.enriched} enriched, ${status.failed} failed`);
          refetch();
        }
        if (status.status === "failed") {
          setRefreshStatus(status.error || "Detail parsing failed");
        }
      } catch (error) {
        setRefreshStatus(error.message);
      }
    }, 1000);

    return () => window.clearInterval(intervalId);
  }, [detailStatus?.status, refetch]);

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <h1>Warsaw Beauty Explorer</h1>
          <p>{salons.length} salons loaded</p>
        </div>
        <div className="refresh-panel">
          <label>
            Salons to scrape
            <input
              min="1"
              max="1000"
              type="number"
              value={salonCount}
              onChange={(event) => setSalonCount(Number(event.target.value))}
            />
          </label>
          <span>{pagesToScrape || 0} pages</span>
          <button className="primary" onClick={startRefresh} disabled={scraperStatus?.status === "running"}>
            <RefreshCw size={16} /> Refresh data
          </button>
          <button className="secondary" onClick={startDetailParsing} disabled={detailStatus?.status === "running"}>
            Parse details
          </button>
        </div>
      </header>

      <div className="workspace">
        <Filters filters={filters} districts={districts} onChange={setFilters} />
        <section className="salon-list" aria-label="Salon list">
          {loading && <p className="state">Loading salons...</p>}
          {error && <p className="state error">{error}</p>}
          {refreshStatus && <p className="state">{refreshStatus}</p>}
          {scraperStatus?.status === "running" && (
            <div className="scraper-progress">
              <div className="scraper-progress__meta">
                <span>{scraperStatus.parsed_count} parsed</span>
                <span>{scraperStatus.remaining_count} left</span>
              </div>
              <div className="scraper-progress__bar" aria-label="Scraper progress">
                <span style={{ width: `${scraperStatus.progress_percent}%` }} />
              </div>
              <p>
                Page {scraperStatus.pages_completed} of {scraperStatus.pages_total}
              </p>
            </div>
          )}
          {detailStatus?.status === "running" && (
            <div className="scraper-progress">
              <div className="scraper-progress__meta">
                <span>{detailStatus.processed} processed</span>
                <span>{detailStatus.remaining} left</span>
              </div>
              <div className="scraper-progress__bar" aria-label="Detail parsing progress">
                <span style={{ width: `${detailStatus.progress_percent}%` }} />
              </div>
              <p>
                Enriched {detailStatus.enriched}, failed {detailStatus.failed}
              </p>
            </div>
          )}
          {!loading && salons.length === 0 && <p className="state">No salons yet. Run the scraper.</p>}
          {salons.map((salon) => (
            <SalonCard
              key={salon.id}
              salon={salon}
              selected={salon.id === selectedSalonId}
              onSelect={setSelectedSalonId}
            />
          ))}
        </section>
        <SalonDetails salonId={selectedSalonId} onSaved={refetch} />
      </div>
    </main>
  );
}
