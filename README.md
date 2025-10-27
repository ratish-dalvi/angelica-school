# Angelica School Tools

## Letter of Recommendation Generator

A Flask web application that generates personalized letters of recommendation in Angelica Goff's voice.

### Quick Start

1. Navigate to the webapp directory:

   ```bash
   cd webapp
   ```

2. Set up your environment variables:

   ```bash
   export OPENAI_API_KEY='your-api-key'
   export OPENAI_API_BASE='your-api-base-url'
   ```

3. Run the application:

   ```bash
   ./run.sh
   ```

4. Open your browser to: <http://localhost:5000>

### Features

- **Web-based form** for entering student details
- **Side-by-side interface** with form and generated letter
- **Real-time editing** - make changes and regenerate instantly
- **Copy to clipboard** functionality
- **Responsive design** for different screen sizes

### Usage

1. Fill out the student information form
2. Generate the initial letter
3. Make edits to any field and regenerate as needed
4. Copy the final letter to clipboard
5. Start a new letter for the next student

See the [webapp README](webapp/README.md) for detailed setup and usage instructions.
Programs for Angelica's school work
