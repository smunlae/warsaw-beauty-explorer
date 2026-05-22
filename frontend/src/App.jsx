import { RefreshCw } from "lucide-react";
import { useMemo, useState } from "react";
import { Filters } from "./components/Filters";
import { SalonCard } from "./components/SalonCard";
import { SalonDetails } from "./components/SalonDetails";
import { refreshScraper, useSalons } from "./hooks/useSalons";

export default function App() {
  const [filters, setFilters] = useState({ q: "", district: "", service: "" });
  const [selectedSalonId, setSelectedSalonId] = useState(null);
  const [refreshStatus, setRefreshStatus] = useState("");
  const { salons, loading, error, refetch } = useSalons(filters);

  const districts = useMemo(() => {
    return [...new Set(salons.map((salon) => salon.district).filter(Boolean))].sort();
  }, [salons]);

  const startRefresh = async () => {
    setRefreshStatus("Starting scraper...");
    try {
      await refreshScraper();
      setRefreshStatus("Scraper started");
    } catch (error) {
      setRefreshStatus(error.message);
    }
  };

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <h1>Warsaw Beauty Explorer</h1>
          <p>{salons.length} salons loaded</p>
        </div>
        <button className="primary" onClick={startRefresh}><RefreshCw size={16} /> Refresh data</button>
      </header>

      <div className="workspace">
        <Filters filters={filters} districts={districts} onChange={setFilters} />
        <section className="salon-list" aria-label="Salon list">
          {loading && <p className="state">Loading salons...</p>}
          {error && <p className="state error">{error}</p>}
          {refreshStatus && <p className="state">{refreshStatus}</p>}
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
