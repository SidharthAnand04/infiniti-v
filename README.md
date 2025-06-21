# Infiniti-V

This project provides a small Flask backend for generating a JSON scene script from a one-sentence prompt. The current code simulates the ∞‑V multi-agent pipeline and can later be extended with real language models.

## Usage

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the server:
   ```bash
   python app.py
   ```
3. Send a POST request to `/generate_scene` with a JSON body containing a `prompt` field.

The response is a list of dialogue and action blocks in the ∞‑VScript format.

### Example

```bash
curl -X POST http://localhost:5000/generate_scene \
  -H "Content-Type: application/json" \
  -d '{"prompt": "A teacher explains gravity to students in a treehouse."}'
```

The server responds with JSON similar to:

```json
[
  {"id": "1", "type": "dialogue", "character": "Teacher", "text": "This is line 1 about A teacher explains gravity to students", "duration": 3.0},
  {"id": "5", "type": "action", "description": "Teacher gestures while speaking.", "timing": "after"}
]
```
