import os
from flask import Flask, request, jsonify, g
from flask_cors import CORS
import sqlite3
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
import pykakasi
import re
import logging
import time

app = Flask(__name__)
CORS(app)

load_dotenv()

DATABASE = 'lyrics_cache.db'
GENIUS_API_KEY = os.getenv('GENIUS_API_KEY')
GENIUS_API_URL = 'https://api.genius.com/search'

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_db():
    # Use Flask application context to cache the connection per request thread
    if 'db_conn' not in g:
        conn = sqlite3.connect(DATABASE, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        g.db_conn = conn
    return g.db_conn

# Close connection after request ends
@app.teardown_appcontext
def close_db(exception=None):
    conn = g.pop('db_conn', None)
    if conn is not None:
        conn.close()

def init_db():
    conn = sqlite3.connect(DATABASE, check_same_thread=False)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS lyrics (
            query TEXT PRIMARY KEY,
            lyrics_text TEXT
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/api/lyrics', methods=['GET'])
def get_lyrics():
    query = request.args.get('q', '').strip()

    if not query:
        logging.warning("Empty query received")
        return jsonify({"error": "Query parameter 'q' is required."}), 400

    if not GENIUS_API_KEY:
        logging.error("Genius API key not configured")
        return jsonify({"error": "Server configuration error: API key missing."}), 500

    conn = get_db()
    cursor = conn.cursor()

    # Check cache first
    cursor.execute('SELECT lyrics_text FROM lyrics WHERE query = ?', (query,))
    cached = cursor.fetchone()

    if cached:
        logging.info(f"Cache hit for query: '{query}'")
        conn.close()
        return jsonify({"lyrics": cached['lyrics_text']})

    logging.info(f"Cache miss for query: '{query}'. Fetching from Genius.")
    # If not in cache, fetch from Genius API
    headers = {'Authorization': f'Bearer {GENIUS_API_KEY}', 'User-Agent': 'Mozilla/5.0'}
    params = {'q': query}

    max_attempts = 3
    backoff = 1
    for attempt in range(max_attempts):
        try:
            response = requests.get(GENIUS_API_URL, headers=headers, params=params, timeout=10)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            if response.status_code != 429:
                break  # success or other error
            logging.warning("Rate limited by Genius API, backing off %s seconds", backoff)
            time.sleep(backoff)
            backoff *= 2  # exponential
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching data for query '{query}': {e}")
            conn.close()
            return jsonify({"error": f"Failed to fetch lyrics from provider: {e}"}), 502 # Bad Gateway

    data = response.json()
    hits = data.get('response', {}).get('hits', [])

    if not hits:
        logging.info(f"No Genius results found for query: '{query}'")
        # Optionally cache 'not found' state to avoid repeated API calls for known misses
        # cursor.execute('INSERT INTO lyrics (query, lyrics_text) VALUES (?, ?)', (query, ''))
        # conn.commit()
        conn.close()
        return jsonify({"lyrics": ""}), 200 # Return empty lyrics, frontend handles 'not found'

    # For simplicity, assume first hit is the desired one
    # A real app might need more logic to pick the right song or scrape lyrics
    # Genius API doesn't directly provide full lyrics easily.
    # This example just returns the song title as a placeholder.
    song_path = hits[0]['result']['path']
    page = requests.get('https://genius.com' + song_path, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
    if page.status_code != 200:
        conn.close()
        return jsonify({"error": "Failed to fetch lyrics from provider."}), 502 # Bad Gateway
    soup = BeautifulSoup(page.text, 'html.parser')
    # Extract lyrics containers for new and old markup
    lyrics_containers = soup.find_all('div', class_=re.compile('Lyrics__Container'))
    if not lyrics_containers:
        lyrics_containers = soup.select('div[data-lyrics-container="true"]')
    lyrics_lines = []
    for c in lyrics_containers:
        # Replace <br> with newline
        for br in c.find_all('br'):
            br.replace_with('\n')
        text = c.get_text(separator='\n').strip()
        lyrics_lines.append(text)
    lyrics_text = '\n'.join(lyrics_lines).strip()
    
    # Fungsi untuk membersihkan tag dan format lirik
    def clean_lyrics(text):
        # Split lirik menjadi baris-baris
        lines = text.split('\n')
        cleaned_lines = []
        
        # Flag untuk mengindikasikan kita telah menemukan baris lirik pertama yang valid
        found_actual_lyrics = False
        after_actual_lyrics = False  # Flag untuk mendeteksi ketika lirik sudah berakhir
        
        # Pola untuk mengenali format non-lirik yang umum
        metadata_patterns = [
            # Metadata spesifik - gunakan pola yang sangat spesifik
            'Contributor', '1 Contributor', '2 Contributors', '3 Contributors',
            'Genius Contributor', 'Genius Contributors',
            'cover of a', 'released on the', 'compilation',
            'Read More', 'View More', 'Translations'
        ]
        
        # Pola bahasa terjemahan yang jelas (sebagai kata tunggal/header, bukan bagian lirik)
        language_patterns = [
            # Format dengan titik dua
            'Translations:', 'Français:', 'Español:', 'Deutsch:', 'Italiano:', 'Português:',
            'Slovenščina:', 'Čeština:', 'Македонски:',
            'Türkçe:', 'Română:', 'Polski:', 'עברית:', 'Ελληνικά:',
            'Nederlands:', 'Dansk:', 'فارسی:', 'العربية:', 'Русский:',
            
            # Format dengan kurung siku
            '[Translations]', '[Français]', '[Español]', '[Deutsch]', '[Italiano]', '[Português]',
            '[Slovenščina]', '[Česky]', '[Македонски]',
            '[Türkçe]', '[Română]', '[Polski]', '[עברית]', '[Ελληνικά]',
            '[Nederlands]', '[Dansk]', '[فارسی]', '[العربية]', '[Русский]',
            
            # Format kata tunggal (tanpa tanda baca)
            'Translations', 'Français', 'Español', 'Deutsch', 'Italiano', 'Português',
            'Slovenščina', 'Česky', 'Македонски',
            'Türkçe', 'Română', 'Polski', 'Hebrew', 'עברית', 'Ελληνικά',
            'Nederlands', 'Dansk', 'فارسی', 'العربية', 'Русский'
        ]
        
        # Hapus baris-baris sampai menemukan lirik yang sesungguhnya dan hentikan setelah metadata akhir
        for line in lines:
            line_stripped = line.strip()
            
            # Jika line kosong, lewati
            if not line_stripped:
                if found_actual_lyrics and not after_actual_lyrics:
                    cleaned_lines.append(line)  # Pertahankan baris kosong jika di tengah lirik
                continue
                
            # Skip header seperti "Song Title Lyrics" sebelum lirik dimulai
            if not found_actual_lyrics and line_stripped.lower().endswith('lyrics') and len(line_stripped.split()) <= 6:
                continue
                
            # Skip baris yang merupakan tag dalam format [tag] atau {tag}
            if line_stripped and ((line_stripped[0] == '[' and ']' in line_stripped) or 
               (line_stripped[0] == '{' and '}' in line_stripped)):
                continue
                
            # Cek apakah ini adalah metadata atau judul bahasa yang jelas
            should_skip = False
            
            # Cek pola metadata umum - harus match exact atau setidaknya sebagai frasa utuh
            for pattern in metadata_patterns:
                if pattern in line_stripped:
                    words = line_stripped.split()
                    # Jika baris hanya berisi 1-3 kata, lebih mungkin metadata/header
                    if len(words) <= 3 or pattern == line_stripped:
                        should_skip = True
                        if found_actual_lyrics:
                            after_actual_lyrics = True
                        break
            
            # Cek pola bahasa (harus lebih ketat untuk menghindari false positive)
            for pattern in language_patterns:
                if pattern == line_stripped or f" {pattern} " in f" {line_stripped} ":
                    should_skip = True
                    if found_actual_lyrics:
                        after_actual_lyrics = True
                    break
                    
            if should_skip:
                continue
            
            # Jika sampai di sini dan belum dalam status after_actual_lyrics, ini adalah lirik valid
            if not after_actual_lyrics:
                found_actual_lyrics = True
                cleaned_lines.append(line)
        
        # Gabungkan kembali baris-baris yang sudah dibersihkan
        return '\n'.join(cleaned_lines)
    
    # Bersihkan lirik
    lyrics_text = clean_lyrics(lyrics_text)
    if not lyrics_text:
        conn.close()
        return jsonify({"error": "Failed to parse lyrics."}), 500
    # Romanisasi teks lirik ke romaji
    kks = pykakasi.kakasi()
    # Konfig mode kanji, hiragana, katakana -> latin
    kks.setMode('J', 'a')
    kks.setMode('H', 'a')
    kks.setMode('K', 'a')
    converter = kks.getConverter()
    romanized = converter.do(lyrics_text)
    logging.info(f"Fetched data for query: '{query}', result: '{romanized}'")
    # Save to cache
    cursor.execute('INSERT INTO lyrics (query, lyrics_text) VALUES (?, ?)', (query, romanized))
    conn.commit()

    conn.close()
    return jsonify({"lyrics": romanized})

if __name__ == '__main__':
    with app.app_context():
        init_db() # Ensure table exists
    app.run(host='0.0.0.0', port=5000, debug=True)
