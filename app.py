# app.py
from flask import Flask, render_template, request, Response, stream_with_context
from flask_cors import CORS
from openai import OpenAI
import json
import os

app = Flask(__name__)

# Initialize the OpenAI client
client = OpenAI(
    api_key=os.environ.get('OPENAI_API_KEY')
)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    option = data['option']
    user_message = data['message']
    
    if option == "Quiz me about":
        prompt = f"Return only valid JSON. No plain text whatsoever. Return only valid JSON. Create a quiz about {user_message} with 3 multiple-choice questions. Return the response as a JSON object with the following structure: {{\"questions\": [{{\"question\": \"...\", \"options\": [\"A. ...\", \"B. ...\", \"C. ...\", \"D. ...\"], \"correct_answer\": \"A\", \"explanation\": \"...\"}}]}}. Ensure the JSON is valid and contains exactly 3 questions. Return only valid JSON."
    elif option == "Give me flashcards about":
        prompt = f"Return only valid JSON. No plain text whatsoever. Return only valid JSON. Create a set of 5 flashcards about {user_message}. Return the response as a JSON object with the following structure: {{\"flashcards\": [{{\"front\": \"...\", \"back\": \"...\"}}]}}. Ensure the JSON is valid and contains exactly 5 flashcards. Return only valid JSON."
    elif option == "Suggest Books about":
        prompt = f"Return only valid JSON. No plain text whatsoever. Return only valid JSON. Provide only 3 simple and obvious book title words about {user_message}. Return the response as a JSON object with the following structure: {{\"searchTerms\": [\"term1\", \"term2\", \"term3\"]}}. Ensure the JSON is valid and contains exactly 3 search terms. Return only valid JSON."
    else:
        prompt = f"{option} {user_message}"
    
    def generate():
        try:
            completion = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an educator for children or a JSON-only provider depending on the situation"},
                    {"role": "user", "content": prompt}
                ],
                stream=True
            )

            full_response = ""
            for chunk in completion:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    yield f"data: {json.dumps({'content': content})}\n\n"
            
            if option in ["Quiz me about", "Give me flashcards about", "Suggest Books about"]:
                try:
                    # Attempt to parse the full response as JSON
                    json.loads(full_response)
                except json.JSONDecodeError:
                    # If parsing fails, yield an error message
                    yield f"data: {json.dumps({'error': 'Failed to generate valid JSON response.'})}\n\n"
            
            yield "data: [DONE]\n\n"
        
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return Response(stream_with_context(generate()), content_type='text/event-stream')

if __name__ == '__main__':
    app.run(debug=True)