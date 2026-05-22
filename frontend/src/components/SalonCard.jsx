import { MapPin, Star } from "lucide-react";

export function SalonCard({ salon, selected, onSelect }) {
  const services = salon.services_offered?.slice(0, 3) ?? [];

  return (
    <button className={`salon-card ${selected ? "is-selected" : ""}`} onClick={() => onSelect(salon.id)}>
      <div className="salon-card__topline">
        <h2>{salon.name}</h2>
        <span className="rating"><Star size={16} /> {salon.rating ?? "No rating"}</span>
      </div>
      <p className="muted"><MapPin size={15} /> {salon.district}</p>
      <p className="reviews">{salon.reviews_count} reviews</p>
      {salon.price_range && <p className="price">{salon.price_range}</p>}
      {services.length > 0 && (
        <div className="chips">
          {services.map((service) => <span key={service}>{service}</span>)}
        </div>
      )}
    </button>
  );
}
