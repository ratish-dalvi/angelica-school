# Letter of Recommendation Generator - Flask Web App

A simple Flask web application that generates personalized letters of recommendation in Angelica Goff's voice.

## Features

- Simple web form to input student details
- Generates recommendation letters using the same logic as the original CLI tool
- Clean, responsive web interface
- One-click copy to clipboard functionality
- No database required - processes forms directly

## Setup

1. Navigate to the webapp directory:
   ```bash
   cd webapp
   ```

2. Set up your environment variables (required for Gemini API):
   ```bash
   export OPENAI_API_KEY='your-api-key'
   export OPENAI_API_BASE='your-api-base-url'
   ```

3. Run the application:
   ```bash
   ./run.sh
   ```

   Or manually:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   python app.py
   ```

4. Open your browser to: http://localhost:5000

## Usage

1. Fill out the form with the student's details (or click **Fill test information** to try it out) and click **Generate letter**.
2. The first draft opens next to a chat. Ask for changes in the chat; each revision becomes a new version of the letter, and you can step back to earlier versions. You can also edit the letter directly.
3. When feedback sounds like a general preference ("I prefer shorter letters"), the chat suggests adding it to the writing style. Click **Add to writing style** to save it.
4. **Copy** or **Download .txt** the letter (the file is named after the student). **Start new letter** clears everything for the next student.

## Writing style

`writing_style.md` holds Angelica's writing style and is sent to the model with every letter. View and edit it on the **Writing style** page (`/style`), which also has a **Download .md** button.

Edits saved in the app are written to `writing_style.md` on the server, so they're lost when a Render instance restarts or redeploys. At the end of a season, download the latest copy and commit it here.

`system_prompt.txt` holds the fixed parts: who Angelica is, the school header, and the signature block.

## Files

- `app.py` - Flask app: pages plus the `/api/generate`, `/api/chat`, and `/api/style` endpoints
- `gemini_client.py` - Gemini API client (OpenAI-compatible)
- `system_prompt.txt` - Role, school header, and signature block
- `writing_style.md` - Angelica's writing style (editable in the app)
- `templates/` - `index.html` (form + chat/letter workspace), `style.html` (writing style editor)
- `static/` - `app.css`, `app.js`
- `requirements.txt` - Python dependencies
- `run.sh` - Setup and run script
