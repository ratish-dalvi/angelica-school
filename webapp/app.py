from flask import Flask, render_template, request, redirect, url_for
import os
from gemini_client import GeminiClient

app = Flask(__name__)

def load_system_prompt():
    """Load the system prompt from file"""
    try:
        with open('system_prompt.txt', 'r', encoding='utf-8') as file:
            return file.read().strip()
    except Exception as e:
        print(f"Error reading system prompt file: {e}")
        return ""

def create_recommendation_prompt(system_prompt, student_data):
    """Create the comprehensive prompt for letter generation"""
    return f"""
{system_prompt}

Now, please write a professional letter of recommendation for {student_data['name']} who is a {student_data['year']} student graduating in {student_data['graduation_date']} and is interested in studying {student_data['area_of_interest']}.

Here are the key details about the student organized into 5 sections:

ACADEMIC CHARACTERISTICS:
{student_data['academic_characteristics']}

SOCIAL/EMOTIONAL CHARACTERISTICS:
{student_data['social_emotional_characteristics']}

OTHER NOTABLE ASPECTS:
{student_data['other_notable_aspects']}

POST-SECONDARY GOALS:
{student_data['post_secondary_goals']}

WHY THEY ARE WELL SUITED FOR THOSE GOALS:
{student_data['suitability_for_goals']}

Write this letter in Angelica's authentic voice, incorporating her typical phrasing, structure, and warmth. Include the proper school header and signature block. Make the letter feel genuine and personal, as if Angelica herself wrote it based on her deep knowledge of the student.
"""

@app.route('/')
def home():
    """Home page with student form"""
    return render_template('form.html')

@app.route('/generate', methods=['POST'])
def generate_letter():
    """Generate and display the recommendation letter"""
    try:
        # Check environment variables first
        if not os.environ.get("OPENAI_API_KEY") or not os.environ.get("OPENAI_API_BASE"):
            return "Error: Missing required environment variables OPENAI_API_KEY and/or OPENAI_API_BASE", 500
        
        # Get form data
        student_data = {
            'name': request.form['name'],
            'area_of_interest': request.form['area_of_interest'],
            'year': request.form['year'],
            'graduation_date': request.form['graduation_date'],
            'academic_characteristics': request.form['academic_characteristics'],
            'social_emotional_characteristics': request.form['social_emotional_characteristics'],
            'other_notable_aspects': request.form['other_notable_aspects'],
            'post_secondary_goals': request.form['post_secondary_goals'],
            'suitability_for_goals': request.form['suitability_for_goals']
        }
        
        # Load system prompt
        system_prompt = load_system_prompt()
        if not system_prompt:
            return "Error: Could not load system prompt", 500
        
        # Generate letter
        client = GeminiClient()
        prompt = create_recommendation_prompt(system_prompt, student_data)
        letter = client.ask_gemini(prompt)
        
        if not letter or letter.startswith("Error"):
            return f"Failed to generate letter: {letter}", 500
        
        return render_template('side_by_side.html', student=student_data, letter=letter)
        
    except Exception as e:
        print(f"Full error details: {e}")
        return f"Error generating letter: {str(e)}", 500

if __name__ == '__main__':
    # Get port from environment variable or default to 5000 for local development
    port = int(os.environ.get('PORT', 5000))
    # Bind to 0.0.0.0 for production (Render) or localhost for local development
    host = '0.0.0.0' if os.environ.get('PORT') else 'localhost'
    app.run(debug=True, host=host, port=port)