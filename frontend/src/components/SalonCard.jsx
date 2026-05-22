import { MapPin } from "lucide-react";
import { RatingStars } from "./RatingStars";

export function SalonCard({ salon, selected, onSelect }) {
  const services = salon.services_offered?.slice(0, 3) ?? [];
  const placeholder = salon.name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("");

  return (
    <button className={`salon-card ${selected ? "is-selected" : ""}`} onClick={() => onSelect(salon.id)}>
      <div className="salon-card__cover">
        {salon.cover_image_url ? (
          <img src={salon.cover_image_url} alt="" loading="lazy" />
        ) : (
          <span>{placeholder || "WB"}</span>
        )}
      </div>
      <div className="salon-card__content">
        <div className="salon-card__topline">
          <h2>{salon.name}</h2>
          <RatingStars rating={salon.rating} />
        </div>
        <p className="muted"><MapPin size={15} /> {salon.district}</p>
        <p className="reviews">{salon.reviews_count} reviews</p>
        {salon.price_range && <p className="price">{salon.price_range}</p>}
        {services.length > 0 && (
          <div className="chips">
            {services.map((service) => <span key={service}>{service}</span>)}
          </div>
        )}
      </div>
    </button>
  );
}
