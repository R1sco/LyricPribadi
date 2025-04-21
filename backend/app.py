import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
CORS(app)

# Placeholder: endpoint pencarian lirik
@app.route('/api/lyrics', methods=['GET'])
def get_lyrics():
    # TODO: Implementasi pencarian lirik Genius & romanisasi Jepang
    return jsonify({'message': 'Endpoint lirik siap'}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)
