export function Filters({ filters, districts, onChange }) {
  return (
    <aside className="filters" aria-label="Salon filters">
      <label>
        Search
        <input
          value={filters.q}
          onChange={(event) => onChange({ ...filters, q: event.target.value })}
          placeholder="Name or address"
        />
      </label>

      <label>
        District
        <select
          value={filters.district}
          onChange={(event) => onChange({ ...filters, district: event.target.value })}
        >
          <option value="">All districts</option>
          {districts.map((district) => (
            <option key={district} value={district}>{district}</option>
          ))}
        </select>
      </label>

      <label>
        Service
        <input
          value={filters.service}
          onChange={(event) => onChange({ ...filters, service: event.target.value })}
          placeholder="Hair, nails, brows"
        />
      </label>

      <label>
        Sort by
        <select
          value={filters.sort_by}
          onChange={(event) => onChange({ ...filters, sort_by: event.target.value })}
        >
          <option value="reviews_count">Reviews</option>
          <option value="rating">Rating</option>
          <option value="name">Name</option>
          <option value="price">Price</option>
        </select>
      </label>
    </aside>
  );
}
