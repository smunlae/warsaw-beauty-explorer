import { ExternalLink, Save } from "lucide-react";
import { useEffect, useState } from "react";
import { fetchSalon, updateSalon } from "../hooks/useSalons";

export function SalonDetails({ salonId, onSaved }) {
  const [salon, setSalon] = useState(null);
  const [form, setForm] = useState(null);
  const [status, setStatus] = useState("");

  useEffect(() => {
    if (!salonId) return;
    setStatus("Loading details...");
    fetchSalon(salonId)
      .then((data) => {
        setSalon(data);
        setForm({
          name: data.name ?? "",
          address: data.address ?? "",
          district: data.district ?? "",
          phone_number: data.phone_number ?? "",
          website_url: data.website_url ?? "",
          social_media_url: data.social_media_url ?? "",
          price_range: data.price_range ?? "",
        });
        setStatus("");
      })
      .catch((error) => setStatus(error.message));
  }, [salonId]);

  if (!salonId) return <section className="details empty">Select a salon</section>;
  if (!salon || !form) return <section className="details empty">{status || "Loading..."}</section>;

  const setField = (field, value) => setForm((current) => ({ ...current, [field]: value }));
  const placeholder = salon.name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("");

  const save = async () => {
    setStatus("Saving...");
    try {
      await updateSalon(salon.id, form);
      setStatus("Saved");
      onSaved();
    } catch (error) {
      setStatus(error.message);
    }
  };

  return (
    <section className="details">
      <div className="details__cover">
        {salon.cover_image_url ? (
          <img src={salon.cover_image_url} alt="" />
        ) : (
          <span>{placeholder || "WB"}</span>
        )}
      </div>

      <div className="details__header">
        <div>
          <h2>{salon.name}</h2>
          <p>{salon.source_name}</p>
        </div>
        {salon.source_url && (
          <a href={salon.source_url} target="_blank" rel="noreferrer" title="Open source page">
            <ExternalLink size={18} />
          </a>
        )}
      </div>

      <div className="form-grid">
        <label>Name<input value={form.name} onChange={(event) => setField("name", event.target.value)} /></label>
        <label>District<input value={form.district} onChange={(event) => setField("district", event.target.value)} /></label>
        <label className="wide">Address<input value={form.address} onChange={(event) => setField("address", event.target.value)} /></label>
        <label>Phone<input value={form.phone_number} onChange={(event) => setField("phone_number", event.target.value)} /></label>
        <label>Price range<input value={form.price_range} onChange={(event) => setField("price_range", event.target.value)} /></label>
        <label className="wide">Website<input value={form.website_url} onChange={(event) => setField("website_url", event.target.value)} /></label>
        <label className="wide">Social media<input value={form.social_media_url} onChange={(event) => setField("social_media_url", event.target.value)} /></label>
      </div>

      <div className="details__actions">
        <button className="primary" onClick={save}><Save size={16} /> Save</button>
        <span>{status}</span>
      </div>
    </section>
  );
}
