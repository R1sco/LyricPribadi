# Electron + React + Flask + SQLite Windsurf Rules

## Description
Workspace rules for a desktop lyrics finder application built with Electron.js (React) frontend, Python Flask backend, and SQLite for caching lyrics.

## Application Rules Focus
- Consistent communication between frontend and backend.
- Secure handling of API keys and sensitive data.
- Maintainable folder and code structure.
- Multi-language lyric processing, including romanization of Japanese lyrics.

## Implementation Examples
- Frontend only fetches lyrics via the Flask API, without direct scraping.
- Backend uses Flask to scrape Genius and caches results in SQLite.
- Japanese songs are auto-romanized before storage and response.
- All API keys are stored in `.env` (excluded from the repository).

## Educational Purposes
This project is intended for educational use to demonstrate:
- Integrating Electron, React, and Flask in a single desktop application.
- Managing state and UI in React using TypeScript and Hooks.
- Using SQLite for local API caching.
- Performing web scraping with BeautifulSoup and robust error handling.
- Implementing API rate limiting and exponential backoff strategies.
- Securing API keys with environment variables.
- Deploying Flask on a VPS using Gunicorn and Nginx.

## Credits
Educational purposes and best practice adaptations for Electron, React, Flask, and SQLite.

## Todo List

- [ ] Add theme toggle
- [ ] Add spotify-like card
- [ ] Add spotify direct link
- [ ] Add language selection dropdown
- [ ] Add romanization of Japanese lyrics