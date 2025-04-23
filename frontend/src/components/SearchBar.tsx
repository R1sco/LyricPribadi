import React, { useRef } from 'react';

interface SearchBarProps {
  query: string;
  setQuery: (value: string) => void;
  isLoading: boolean;
  onSearch: (e: React.FormEvent<HTMLFormElement> | React.MouseEvent<HTMLButtonElement>) => void;
}

const SearchBar: React.FC<SearchBarProps> = ({ query, setQuery, isLoading, onSearch }) => {
  const inputRef = useRef<HTMLInputElement>(null);
  return (
    <form className="search-container mb-4" onSubmit={onSearch}>
      <input
        ref={inputRef}
        type="text"
        className="form-control form-control-lg text-center"
        placeholder="Enter song or lyrics name"
        aria-label="Enter song or lyrics name"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        disabled={isLoading}
      />
      <button
        className="btn btn-primary search-button-inside"
        type="submit"
        onClick={onSearch}
        disabled={isLoading}
      >
        {isLoading ? (
          <>
            <span className="spinner-border spinner-border-sm text-light me-2" role="status" aria-hidden="true"></span>
            Searching...
          </>
        ) : (
          'Get Lyrics'
        )}
      </button>
    </form>
  );
};

export default SearchBar;
