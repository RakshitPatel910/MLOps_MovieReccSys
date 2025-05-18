// movieHelpers.js
import { movieDB } from '../serverdata/movieDB.js';

export function getMovieTitle(movieId) {
  return movieDB[movieId] || 'Unknown Movie';
}

export function enhanceWatchlist(watchlist) {
  return watchlist.map(item => ({
    ...item,
    title: getMovieTitle(item.movie_id.toString()) // Convert to string if needed
  }));
}