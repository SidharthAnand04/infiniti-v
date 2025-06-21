"""Flask entry point for the ∞‑V script generation pipeline."""

import os
from flask import Flask, request, jsonify
from agents import run_pipeline

app = Flask(__name__)

@app.route('/generate_scene', methods=['POST'])
def generate_scene():
    """Generate a script from a single-sentence prompt."""

    data = request.get_json(silent=True)
    if not data or 'prompt' not in data:
        return jsonify({'error': 'Missing prompt'}), 400

    script = run_pipeline(data['prompt'])
    return jsonify(script)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
