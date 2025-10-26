"""Letter of Recommendation Generator

This module handles loading student details and generating recommendation letters
using Angelica Goff's voice and perspective as a global history teacher.
"""
import yaml
from typing import Dict, Any
from gemini_client import GeminiClient


def create_recommendation_prompt(system_prompt: str, basic_info: Dict[str, Any], 
                               academic: str, social_emotional: str, other: str, 
                               goals: str, suitability: str) -> str:
    """Create the comprehensive prompt for letter generation"""
    return f"""
{system_prompt}

Now, please write a professional letter of recommendation for {basic_info.get('name', 'the student')} who is a senior student graduating in {basic_info.get('graduation_date', '')} and is interested in studying {basic_info.get('area_of_interest', 'their chosen field')}.

Here are the key details about the student organized into 5 sections:

ACADEMIC CHARACTERISTICS:
{academic}

SOCIAL/EMOTIONAL CHARACTERISTICS:
{social_emotional}

OTHER NOTABLE ASPECTS:
{other}

POST-SECONDARY GOALS:
{goals}

WHY THEY ARE WELL SUITED FOR THOSE GOALS:
{suitability}

Write this letter in Angelica's authentic voice, incorporating her typical phrasing, structure, and warmth. Include the proper school header and signature block. Make the letter feel genuine and personal, as if Angelica herself wrote it based on her deep knowledge of the student.
"""


def load_system_prompt(prompt_path: str = "system_prompt.txt") -> str:
    """Load the system prompt from file"""
    try:
        with open(prompt_path, 'r', encoding='utf-8') as file:
            return file.read().strip()
    except FileNotFoundError:
        print(f"System prompt file not found: {prompt_path}")
        return ""
    except Exception as e:
        print(f"Error reading system prompt file: {e}")
        return ""


def load_student_details(yaml_path: str = "details.yaml") -> Dict[str, Any]:
    """Load student details from YAML file"""
    try:
        with open(yaml_path, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        print(f"Details file not found: {yaml_path}")
        return {}
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file: {e}")
        return {}


def generate_recommendation_letter(client: GeminiClient, student_details: Dict[str, Any], system_prompt: str) -> str:
    """Generate a recommendation letter based on student details"""
    if not student_details:
        return "Error: No student details provided"
    
    # Extract information from the structured YAML
    basic_info = student_details.get('student_basic_info', {})
    academic = student_details.get('academic_characteristics', '')
    social_emotional = student_details.get('social_emotional_characteristics', '')
    other = student_details.get('other_notable_aspects', '')
    goals = student_details.get('post_secondary_goals', '')
    suitability = student_details.get('suitability_for_goals', '')
    
    # Create the prompt using the dedicated function
    prompt = create_recommendation_prompt(
        system_prompt, basic_info, academic, social_emotional, 
        other, goals, suitability
    )
    
    return client.ask_gemini(prompt)


def save_letter_to_file(letter: str, student_name: str) -> str:
    """Save the generated letter to a file"""
    output_file = f"recommendation_letter_{student_name.replace(' ', '_').lower()}.txt"
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(letter)
        return output_file
    except Exception as e:
        print(f"Could not save letter to file: {e}")
        return ""


def main():
    """Main function to generate a recommendation letter"""
    print("Generating Letter of Recommendation...")
    
    # Initialize Gemini client
    client = GeminiClient()
    
    # Load system prompt
    system_prompt = load_system_prompt()
    if not system_prompt:
        print("Error: Could not load system prompt from system_prompt.txt")
        return
    
    # Load student details
    details = load_student_details()
    if not details:
        print("Error: Could not load student details from details.yaml")
        return
    
    student_name = details.get('student_basic_info', {}).get('name', 'Unknown')
    print(f"Generating letter for: {student_name}")
    
    # Generate the recommendation letter
    letter = generate_recommendation_letter(client, details, system_prompt)
    
    if letter:
        print("\n" + "="*60)
        print("GENERATED LETTER OF RECOMMENDATION")
        print("="*60)
        print(letter)
        print("="*60)
        
        # Save to file
        output_file = save_letter_to_file(letter, student_name)
        if output_file:
            print(f"\nLetter saved to: {output_file}")
    else:
        print("Failed to generate recommendation letter.")


if __name__ == "__main__":
    main()