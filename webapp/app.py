from flask import Flask, jsonify, render_template, request
import logging
import os
import re
import tempfile
import openai
from gemini_client import GeminiClient

# Configure before creating the app so Flask's logger uses this format too
logging.basicConfig(
    level=os.environ.get('LOG_LEVEL', 'INFO').upper(),
    format='%(asctime)s %(levelname)s %(name)s: %(message)s',
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SYSTEM_PROMPT_PATH = os.path.join(BASE_DIR, 'system_prompt.txt')
WRITING_STYLE_PATH = os.path.join(BASE_DIR, 'writing_style.md')

# Style suggestions accepted from the chat are collected under this heading
FEEDBACK_HEADING = '## Notes from letter feedback'

REQUIRED_FIELDS = [
    'name', 'area_of_interest', 'year', 'graduation_date',
    'academic_characteristics', 'social_emotional_characteristics', 'other_notable_aspects',
    'post_secondary_goals', 'suitability_for_goals',
]
OPTIONAL_FIELDS = ['pronouns', 'angelica_instructions']

# How many earlier chat turns to send back to the model
MAX_HISTORY_MESSAGES = 20

CHAT_INSTRUCTIONS = """# YOUR ROLE IN THIS CONVERSATION

You've already written a draft of this student's letter, and Angelica is now reviewing it with you. She may ask for changes, ask a question, or give general feedback. Each of her messages comes with the current version of the letter, which may include edits she made herself; keep those edits unless she asks otherwise.

Answer in this exact format, using these tags:

<reply>
Your reply to Angelica: one to three sentences, plain text. If you changed the letter, say briefly what you changed. If her request is unclear, ask a question instead of guessing.
</reply>
<letter>
The complete revised letter, from header to signature. Include this only when you changed the letter; leave the tag out entirely otherwise.
</letter>
<style_suggestion>
One concise guideline, written as an instruction (for example: "Keep letters to one page."), to add to her writing style guide. Include this only when her feedback is a general preference about how she writes that would apply to letters for other students too, not a fact or request specific to this student, and the style guide doesn't already say it. Always include it when she explicitly asks to update her writing style. When you include it, mention in your reply that you've suggested adding it to her writing style. Leave the tag out entirely otherwise.
</style_suggestion>"""


def read_text(path):
    with open(path, 'r', encoding='utf-8') as file:
        return file.read().strip()


def read_writing_style():
    try:
        return read_text(WRITING_STYLE_PATH)
    except FileNotFoundError:
        return ''


def write_writing_style(content):
    # Write to a temp file and swap it in, so a crash mid-write can't leave a truncated style guide
    fd, tmp_path = tempfile.mkstemp(dir=BASE_DIR, suffix='.tmp')
    with os.fdopen(fd, 'w', encoding='utf-8') as file:
        file.write(content.strip() + '\n')
    os.replace(tmp_path, WRITING_STYLE_PATH)


def add_style_note(style, note):
    """Add a bullet to the feedback-notes section, creating the section if needed"""
    note = ' '.join(note.split())
    start = style.find(FEEDBACK_HEADING)
    if start == -1:
        return f"{style}\n\n{FEEDBACK_HEADING}\n\n- {note}"
    # Insert at the end of the section, before the next heading if Angelica added one after it
    end = style.find('\n#', start + len(FEEDBACK_HEADING))
    if end == -1:
        end = len(style)
    return f"{style[:end].rstrip()}\n- {note}\n{style[end:]}"


def build_system_prompt():
    return f"{read_text(SYSTEM_PROMPT_PATH)}\n\n# ANGELICA'S WRITING STYLE GUIDE\n\n{read_writing_style()}"


def parse_student(data):
    """Pull the student fields out of a request body. Returns (student, error)."""
    if not isinstance(data, dict):
        return None, 'Missing student details.'
    student = {field: str(data.get(field) or '').strip() for field in REQUIRED_FIELDS + OPTIONAL_FIELDS}
    missing = [field for field in REQUIRED_FIELDS if not student[field]]
    if missing:
        return None, f"Missing required fields: {', '.join(missing)}"
    return student, None


def describe_student(student):
    """Format the student's details for the prompt"""
    pronouns = student['pronouns'] or "not given (use the student's name and they/them)"
    description = f"""Name: {student['name']}
Pronouns: {pronouns}
Year: {student['year']}
Graduation date: {student['graduation_date']}
Area of interest: {student['area_of_interest']}

ACADEMIC CHARACTERISTICS:
{student['academic_characteristics']}

SOCIAL/EMOTIONAL CHARACTERISTICS:
{student['social_emotional_characteristics']}

OTHER NOTABLE ASPECTS:
{student['other_notable_aspects']}

POST-SECONDARY GOALS:
{student['post_secondary_goals']}

WHY THEY ARE WELL SUITED FOR THOSE GOALS:
{student['suitability_for_goals']}"""

    if student['angelica_instructions']:
        description += f"""

*** SPECIAL INSTRUCTIONS FROM ANGELICA FOR THIS LETTER ***
{student['angelica_instructions']}
*** END SPECIAL INSTRUCTIONS ***"""

    return description


def model_error_message(error, action):
    """A message for the page; temporary model outages get a plain-language one"""
    # 429 rate limits, 5xx errors like 503 "high demand", timeouts, and network failures
    if isinstance(error, (openai.RateLimitError, openai.InternalServerError, openai.APIConnectionError)):
        return 'The AI model is busy or unreachable right now. Wait a minute and try again.'
    return f'{action}: {error}'


def extract_tag(text, tag):
    match = re.search(rf'<{tag}>(.*?)</{tag}>', text, re.DOTALL)
    return match.group(1).strip() if match else ''


def parse_chat_response(text):
    reply = extract_tag(text, 'reply')
    letter = extract_tag(text, 'letter')
    style_suggestion = extract_tag(text, 'style_suggestion')
    if not reply:
        if letter:
            reply = "I've updated the letter."
        elif not style_suggestion:
            # The model ignored the format; show whatever it said as the reply
            logger.warning('Chat response had no <reply>, <letter>, or <style_suggestion> tags; using raw text')
            reply = text.strip()
    return {
        'reply': reply,
        'letter': letter or None,
        'style_suggestion': style_suggestion or None,
    }


@app.route('/')
def home():
    """Form for a new letter, and the chat + letter workspace once one is generated"""
    return render_template('index.html')


@app.route('/style')
def style_page():
    """View and edit Angelica's writing style guide"""
    return render_template('style.html', content=read_writing_style())


@app.post('/api/generate')
def api_generate():
    """Write the first draft of a letter"""
    student, error = parse_student((request.get_json(silent=True) or {}).get('student'))
    if error:
        return jsonify(error=error), 400

    prompt = f"""Write a letter of recommendation for this student.

{describe_student(student)}

Return only the letter, with nothing before or after it."""

    try:
        letter = GeminiClient().complete([
            {'role': 'system', 'content': build_system_prompt()},
            {'role': 'user', 'content': prompt},
        ])
    except Exception as e:
        logger.exception('Letter generation failed')
        return jsonify(error=model_error_message(e, 'Could not generate the letter')), 502

    return jsonify(letter=letter)


@app.post('/api/chat')
def api_chat():
    """Respond to Angelica's feedback, revising the letter if she asked for changes"""
    data = request.get_json(silent=True) or {}
    student, error = parse_student(data.get('student'))
    if error:
        return jsonify(error=error), 400

    letter = str(data.get('letter') or '').strip()
    message = str(data.get('message') or '').strip()
    if not letter or not message:
        return jsonify(error='Both the current letter and a message are required.'), 400

    try:
        system_prompt = f"{build_system_prompt()}\n\n# THE STUDENT\n\n{describe_student(student)}\n\n{CHAT_INSTRUCTIONS}"
        messages = [{'role': 'system', 'content': system_prompt}]
        for turn in (data.get('history') or [])[-MAX_HISTORY_MESSAGES:]:
            if isinstance(turn, dict) and turn.get('role') in ('user', 'assistant') and turn.get('content'):
                messages.append({'role': turn['role'], 'content': str(turn['content'])})
        messages.append({'role': 'user', 'content': f"CURRENT LETTER:\n{letter}\n\nANGELICA'S MESSAGE:\n{message}"})

        response = GeminiClient().complete(messages)
    except Exception as e:
        logger.exception('Chat request failed')
        return jsonify(error=model_error_message(e, 'Could not reach the model')), 502

    return jsonify(parse_chat_response(response))


@app.get('/api/style')
def get_style():
    return jsonify(content=read_writing_style())


@app.put('/api/style')
def save_style():
    content = str((request.get_json(silent=True) or {}).get('content') or '')
    if not content.strip():
        return jsonify(error="The writing style can't be empty."), 400
    try:
        write_writing_style(content)
    except OSError as e:
        logger.exception('Could not save the writing style')
        return jsonify(error=f'Could not save the writing style: {e}'), 500
    return jsonify(content=read_writing_style())


@app.post('/api/style/notes')
def add_style_note_route():
    """Add a guideline suggested in the chat to the writing style"""
    note = str((request.get_json(silent=True) or {}).get('note') or '').strip()
    if not note:
        return jsonify(error='The note is empty.'), 400
    try:
        write_writing_style(add_style_note(read_writing_style(), note))
    except OSError as e:
        logger.exception('Could not add a note to the writing style')
        return jsonify(error=f'Could not save the writing style: {e}'), 500
    return jsonify(content=read_writing_style())


if __name__ == '__main__':
    # Get port from environment variable or default to 5000 for local development
    port = int(os.environ.get('PORT', 5000))
    # Bind to 0.0.0.0 for production (Render) or localhost for local development
    host = '0.0.0.0' if os.environ.get('PORT') else 'localhost'
    app.run(debug=True, host=host, port=port)
