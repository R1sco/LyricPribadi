// React 17+ tidak memerlukan import React untuk JSX
// @ts-ignore - Mengabaikan error TypeScript untuk unused imports
import { useState } from 'react';
import './App.css';
import SearchBar from './components/SearchBar';
import LyricsCard from './components/LyricsCard';

function App() {
  const [query, setQuery] = useState('');
  const [lyrics, setLyrics] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [darkMode, setDarkMode] = useState(true);

  const fetchLyrics = async () => {
    if (!query.trim()) return; // Don't search if query is empty
    setIsLoading(true);
    setError(null);
    setLyrics(''); // Clear previous lyrics

    try {
      const response = await fetch(`/api/lyrics?query=${encodeURIComponent(query)}`);
      const data = await response.json();
      if (response.ok) {
        setLyrics(data.lyrics || 'Lyrics not found.'); // Handle empty lyrics from backend
      } else {
        setError(data.error || 'Failed to fetch lyrics.');
      }
    } catch (error) {
      setError('An error occurred while connecting to the server.');
    } finally {
      setIsLoading(false);
    }
  };

  // Fungsi untuk mengganti tema dan menyimpan preferensi ke localStorage
  const toggleTheme = () => {
    const link = document.getElementById('theme-link') as HTMLLinkElement | null;
    if (!link) return;
    if (darkMode) {
      link.href = 'https://cdn.jsdelivr.net/npm/bootswatch@5.3.2/lux/bootstrap.min.css';
    } else {
      link.href = 'https://cdn.jsdelivr.net/npm/bootswatch@5.3.2/darkly/bootstrap.min.css';
    }
    // Toggle dark mode dan simpan ke localStorage
    const newDarkMode = !darkMode;
    setDarkMode(newDarkMode);
    localStorage.setItem('darkMode', String(newDarkMode));
  };

  return (
    <div className={`container-fluid d-flex flex-column justify-content-center align-items-center min-vh-100 py-4 position-relative ${darkMode ? 'dark-mode' : 'light-mode'}`}>
      <button className="btn theme-btn position-absolute top-0 end-0 m-3" onClick={toggleTheme} aria-label="Toggle Theme">
        {darkMode ? <span role="img" aria-label="Light Mode">☀️</span> : <span role="img" aria-label="Dark Mode">🌙</span>}
      </button>
      <h1 className="text-center mb-4">Lyrics Finder</h1>
      <SearchBar
        query={query}
        setQuery={(value) => setQuery(value)}
        isLoading={isLoading}
        onSearch={(e) => { e.preventDefault(); fetchLyrics(); }}
      />
      
      {error && <div className="alert alert-danger mb-4">{error}</div>}
      
      {lyrics && <LyricsCard lyrics={lyrics} />}
    </div>
  );
}

export default App;
