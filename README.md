# Electron + React + Flask + SQLite Windsurf Rules

## Deskripsi
Aturan workspace untuk aplikasi desktop lirik lagu global, menggunakan Electron.js (React) sebagai frontend, Python Flask sebagai backend API lokal, dan SQLite sebagai database cache lirik.

## Fokus Aturan
- Konsistensi komunikasi antara frontend-backend.
- Keamanan API Key dan data sensitif.
- Struktur kode dan folder yang maintainable.
- Penanganan lirik multi-bahasa, khususnya romanisasi lirik Jepang.

## Contoh Penerapan
- Frontend hanya melakukan fetch ke endpoint Flask, tidak scraping langsung.
- Backend Flask melakukan scraping Genius, lalu simpan hasil ke SQLite.
- Untuk lagu Jepang, backend otomatis romanisasi sebelum simpan/return ke frontend.
- Semua API Key disimpan di `.env` (tidak di repo).

## Credits
Adaptasi dari best practice Electron, React, Flask, dan SQLite.