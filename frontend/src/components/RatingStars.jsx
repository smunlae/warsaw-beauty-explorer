const STAR_COUNT = 5;

export function RatingStars({ rating }) {
  if (rating === null || rating === undefined) {
    return <span className="rating-stars rating-stars--empty">No rating</span>;
  }

  const normalizedRating = Math.max(0, Math.min(STAR_COUNT, Number(rating)));
  const fillWidth = `${(normalizedRating / STAR_COUNT) * 100}%`;

  return (
    <span className="rating-stars" aria-label={`Rating ${normalizedRating.toFixed(2)} out of 5`}>
      <span className="rating-stars__stack" aria-hidden="true">
        <span className="rating-stars__base">★★★★★</span>
        <span className="rating-stars__fill" style={{ width: fillWidth }}>★★★★★</span>
      </span>
      <span className="rating-stars__value">{normalizedRating.toFixed(2)}</span>
    </span>
  );
}
