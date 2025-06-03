from flask import Flask, request, jsonify, g
from flask_cors import CORS
import sqlite3
from dotenv import load_dotenv
import os
import requests
from bs4 import BeautifulSoup
import pykakasi
import re
import logging
import time
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)
CORS(app)

# Configure rate limiter
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
    strategy="fixed-window", # Alternatives: moving-window, fixed-window-elastic-expiry
)

# Custom error handler for rate limiting
@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({
        'error': 'Batas permintaan terlampaui',
        'message': 'Terlalu banyak permintaan. Silakan coba lagi nanti.',
        'retry_after': e.description
    }), 429

# Security headers middleware
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

load_dotenv()

DATABASE = '/tmp/lyrics_cache.db'  # Vercel uses /tmp for writable storage
GENIUS_API_KEY = os.getenv('GENIUS_API_KEY')
GENIUS_API_URL = 'https://api.genius.com/search'

# Validasi API key
if not GENIUS_API_KEY:
    logging.error("GENIUS_API_KEY tidak ditemukan di environment variables. Aplikasi mungkin tidak berfungsi dengan benar.")
    # Kita tidak menghentikan aplikasi, tapi akan mengembalikan error yang jelas saat API dipanggil

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

@app.route('/api/debug', methods=['GET'])
def debug():
    """Endpoint untuk debugging status API"""
    has_api_key = bool(GENIUS_API_KEY)
    return jsonify({
        'status': 'ok',
        'has_api_key': has_api_key,
        'environment': os.environ.get('VERCEL_ENV', 'development'),
        'database_path': DATABASE
    })

@app.route('/api/lyrics', methods=['GET'])
@limiter.limit("5 per minute")
def get_lyrics():
    # Periksa API key terlebih dahulu
    if not GENIUS_API_KEY:
        return jsonify({
            'error': 'API key tidak dikonfigurasi. Harap konfigurasikan GENIUS_API_KEY di environment variables Vercel.'
        }), 500
        
    query = request.args.get('query', '')
    if not query:
        return jsonify({'error': 'No query provided'}), 400
    
    # Check cache first
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT lyrics_text FROM lyrics WHERE query = ?', (query,))
    cached_result = cursor.fetchone()
    
    if cached_result:
        logging.info(f"Cache hit for query: {query}")
        return jsonify({'lyrics': cached_result['lyrics_text']})
    
    # Not in cache, fetch from Genius API
    logging.info(f"Cache miss for query: {query}, fetching from API")
    
    # Search for song
    headers = {'Authorization': f'Bearer {GENIUS_API_KEY}'}
    params = {'q': query}
    
    try:
        response = requests.get(GENIUS_API_URL, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        
        if 'response' not in data or not data['response']['hits']:
            return jsonify({'error': 'No results found'}), 404
        
        # Get the first hit's URL
        song_url = data['response']['hits'][0]['result']['url']
        
        # Scrape lyrics from the URL
        lyrics = scrape_lyrics(song_url)
        
        if lyrics:
            # Cache the result
            cursor.execute('INSERT OR REPLACE INTO lyrics (query, lyrics_text) VALUES (?, ?)', 
                          (query, lyrics))
            conn.commit()
            
            return jsonify({'lyrics': lyrics})
        else:
            return jsonify({'error': 'Could not extract lyrics'}), 500
            
    except requests.exceptions.RequestException as e:
        logging.error(f"API request error: {str(e)}")
        return jsonify({'error': f'API request failed: {str(e)}'}), 500
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500

def scrape_lyrics(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find lyrics container
        lyrics_container = soup.find('div', class_=lambda c: c and 'Lyrics__Container' in c)
        
        if not lyrics_container:
            return None
        
        # Process lyrics
        lyrics_text = ''
        for element in lyrics_container.descendants:
            if element.name == 'br':
                lyrics_text += '\n'
            elif element.string:
                lyrics_text += element.string
        
        # Clean up lyrics
        lyrics_text = re.sub(r'\[.*?\]', '', lyrics_text)  # Remove [Verse], [Chorus], etc.
        lyrics_text = re.sub(r'\n{3,}', '\n\n', lyrics_text)  # Normalize newlines
        lyrics_text = lyrics_text.strip()
        
        return lyrics_text
    
    except Exception as e:
        logging.error(f"Scraping error: {str(e)}")
        return None

# Initialize database
with app.app_context():
    init_db()


