from flask import Flask, render_template, request, jsonify
from markupsafe import Markup
from openai import OpenAI
import os
import logging
import glob
import re

# Custom function to read API key from .env file
def read_api_key_from_file():
    try:
        with open(".env", "r") as f:
            content = f.read()
            for line in content.split('\n'):
                if line.startswith("OPENAI_API_KEY="):
                    return line.split("=", 1)[1].strip()
    except Exception as e:
        logging.error(f"Error reading API key from .env file: {e}")
        return None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure logging for ratings
ratings_logger = logging.getLogger('ratings')
ratings_logger.setLevel(logging.INFO)
ratings_handler = logging.FileHandler('ratings.log')
ratings_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
ratings_logger.addHandler(ratings_handler)

# Initialize Flask app
app = Flask(__name__)

# Hotel booking URLs with exact locations
HOTEL_BOOKING_URLS = {
    "Plaza Hotel": "https://www.aghotels.co.uk/locations/#chorley",  # Chorley, Preston
    "Fortune Hotel": "https://www.aghotels.co.uk/locations/#huddersfield",  # Huddersfield, Yorkshire
    "The Stuart Hotel": "https://www.aghotels.co.uk/locations/#derby",  # Derby, Derbyshire
    "The Milestone Hotel": "https://www.aghotels.co.uk/locations/#peterborough",  # Peterborough, Cambridgeshire
    "Bluewaters Hotel": "https://www.aghotels.co.uk/locations/#blackpool",  # Blackpool, Lancashire
    "The Crown Hotel": "https://www.aghotels.co.uk/locations/#london",  # Cricklewood, London
    "ibis Castleford Hotel": "https://www.aghotels.co.uk/locations/#wakefield",  # Castleford, Wakefield
    "Pinewood Hotel": "https://www.aghotels.co.uk/locations/#manchester",  # Wilmslow, Manchester
    "Embassy Hotel": "https://www.aghotels.co.uk/locations/#newcastle",  # Gateshead, Newcastle
    "The Magnum Hotel": "https://www.aghotels.co.uk/locations/#sunderland",  # Sunderland, Tyne and Wear
    "Casa Mere Hotel": "https://www.aghotels.co.uk/locations/#knutsford",  # Knutsford, Cheshire
    "Lakeside Hotel": "https://www.aghotels.co.uk/locations/#sthelens",  # St Helens, Merseyside
    "Orchid Hotel": "https://www.aghotels.co.uk/locations/#epsom",  # Epsom, London
    "The Lakeland Hotel": "https://www.aghotels.co.uk/locations/#lakedistrict"  # Kendal, Lake District
}

def format_booking_button(hotel_name, url):
    # Get the location from the URL (after the #)
    location = url.split('#')[-1].capitalize()
    
    # Map of special location display names
    location_display = {
        'london': 'Cricklewood, London',
        'chorley': 'Chorley, Preston',
        'huddersfield': 'Huddersfield, Yorkshire',
        'derby': 'Derby, Derbyshire',
        'peterborough': 'Peterborough, Cambridgeshire',
        'blackpool': 'Blackpool, Lancashire',
        'wakefield': 'Castleford, Wakefield',
        'manchester': 'Wilmslow, Manchester',
        'newcastle': 'Gateshead, Newcastle',
        'sunderland': 'Sunderland, Tyne and Wear',
        'knutsford': 'Knutsford, Cheshire',
        'sthelens': 'St Helens, Merseyside',
        'epsom': 'Epsom, London',
        'lakedistrict': 'Kendal, Lake District'
    }
    
    location_text = location_display.get(location.lower(), location)
    
    # Use direct href for simpler operation
    clean_url = url.replace('"', '&quot;').replace("'", "&#39;")
    
    # Simplified button implementation using direct link
    return f'''
        <div class="hotel-card">
            <h4 class="hotel-location">{location_text}</h4>
            <h3 class="hotel-name">{hotel_name}</h3>
            <a href="{clean_url}" 
               class="book-now-btn" 
               target="_blank"
               rel="noopener">
                BOOK NOW
            </a>
        </div>
    '''

# Initialize OpenAI client
api_key = read_api_key_from_file()
if not api_key:
    raise ValueError("Failed to read OpenAI API key from .env file")

client = OpenAI(api_key=api_key)
logger.info("OpenAI client initialized with key starting with: %s...", api_key[:10])

def load_hotel_data():
    hotel_data = {}
    
    # Get all .txt files from the data directory
    data_files = glob.glob('data/*.txt')
    
    for filepath in data_files:
        try:
            # Skip .DS_Store and any other hidden files
            if os.path.basename(filepath).startswith('.'):
                continue
                
            # Get the category name from the filename (without .txt extension)
            category = os.path.splitext(os.path.basename(filepath))[0]
            
            with open(filepath, 'r') as file:
                content = file.read()
                hotel_data[category] = content
                logger.info(f"Loaded {category} data: {len(content)} characters")
        except Exception as e:
            logger.error(f"Error loading {filepath}: {str(e)}")
            hotel_data[category] = ""
    
    return hotel_data

# Load hotel data
HOTEL_DATA = load_hotel_data()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    try:
        # Basic request validation
        if not request.is_json:
            logger.error("Invalid request: Not JSON")
            return jsonify({"error": "Invalid request format", "answer": "Please send a valid JSON request"}), 400

        question = request.json.get('question')
        if not question:
            logger.error("Invalid request: No question provided")
            return jsonify({"error": "No question provided", "answer": "Please provide a question"}), 400

        # Limit question length to prevent excessive processing
        if len(question) > 1000:
            logger.warning("Question too long: %d characters", len(question))
            return jsonify({"error": "Question too long", "answer": "Please keep your question under 1000 characters"}), 400

        logger.info("Received question: %s", question)

        # Create system message with all available data
        system_message = """You are an AI assistant for AG Hotels. Your job is to provide detailed, helpful information based on the hotel data provided to you.

IMPORTANT INSTRUCTIONS:
1. Use ONLY the information provided in the data files to answer questions.
2. DO NOT say "this information is not available" when information exists in the data files.
3. Make sure to ALWAYS search through ALL the data before responding.
4. The location.txt file contains details about hotel rooms, suites, and amenities.
5. The weddings.txt file contains information about wedding venues and packages.
6. The hotel_data.txt file contains general information about AG Hotels.

When responding about hotels, include:
- Full location name
- Hotel name
- Booking button (which will be automatically inserted)
- Relevant details from the data provided

Be thorough in searching the data for relevant information. If you're asked about suites at The Crown Hotel, for example, search through the location.txt data for information about The Crown Hotel and its suites."""

        # Truncate system message if too long
        if len(system_message) > 100000:
            logger.warning("System message too long, truncating")
            # Keep the important parts and instructions
            important_parts = system_message.split("\n=== ")
            truncated_message = important_parts[0] + "\n=== "  # Keep initial part
            
            # Add HOTEL DATA (truncated)
            truncated_message += "IMPORTANT INSTRUCTIONS ===\n"
            truncated_message += "\n".join(system_message.split("\nBe polite")[1:])
            
            system_message = truncated_message

        # Get response from OpenAI with error handling
        try:
            logger.info("Sending request to OpenAI")
            
            # Structured prompt for GPT-4o with maximum precision
            messages = [
                {"role": "system", "content": """You are an AI assistant for AG Hotels. Your job is to provide detailed, helpful information based on the hotel data provided to you.

IMPORTANT INSTRUCTIONS:
1. Use ONLY the information provided in the data files to answer questions.
2. DO NOT say "this information is not available" when information exists in the data files.
3. Make sure to ALWAYS search through ALL the data before responding.
4. The location.txt file contains details about hotel rooms, suites, and amenities.
5. The weddings.txt file contains information about wedding venues and packages.
6. The hotel_data.txt file contains general information about AG Hotels.

When responding about hotels, include:
- Full location name
- Hotel name
- Booking button (which will be automatically inserted)
- Relevant details from the data provided

Be thorough in searching the data for relevant information. If you're asked about suites at The Crown Hotel, for example, search through the location.txt data for information about The Crown Hotel and its suites."""},
                
                {"role": "user", "content": f"""Customer question: {question}

Here is the complete data to search through:

=== LOCATION DATA ===
{HOTEL_DATA.get('location', '')}

=== WEDDINGS DATA ===
{HOTEL_DATA.get('weddings', '')}

=== HOTEL_DATA ===
{HOTEL_DATA.get('hotel_data', '')}

Please provide a helpful, detailed answer based on the above information. Do not say information is unavailable if it exists in the data."""}
            ]
            
            response = client.chat.completions.create(
                model="gpt-4o",  # Using full GPT-4o model for highest quality responses
                messages=messages,
                temperature=0.7,  # Increased temperature for more varied responses
                max_tokens=1000,   # Increased token limit for more comprehensive responses
                presence_penalty=0.1,  # Reduced penalty for more focused responses
                frequency_penalty=0.2,  # Maintaining diversity
                top_p=0.8  # Narrowing probability distribution for more focused generation
            )

            # Process the response
            if not response or not response.choices or len(response.choices) == 0:
                logger.error("Empty response from OpenAI")
                return jsonify({
                    "error": "Received empty response from AI service",
                    "answer": "I apologize, but I didn't receive a proper response. Please try again."
                }), 500

            answer = response.choices[0].message.content
            
            if not answer or answer.strip() == "":
                logger.error("Empty answer content from OpenAI")
                # Fallback to a simple response
                answer = "I apologize, but I'm having trouble generating a specific response. Please try asking your question in a different way, or ask about our hotel locations, rooms, or facilities."
            
            # Check if the answer mentions any hotel names and add booking buttons if needed
            for hotel_name, url in HOTEL_BOOKING_URLS.items():
                # More precise pattern matching to avoid partial matches
                pattern = r'\b' + re.escape(hotel_name) + r'\b'
                if re.search(pattern, answer) and f'class="book-now-btn"' not in answer:
                    # Add booking button if not already present
                    location = url.split('#')[-1].capitalize()
                    location_display = {
                        'london': 'Cricklewood, London',
                        'chorley': 'Chorley, Preston',
                        'huddersfield': 'Huddersfield, Yorkshire',
                        'derby': 'Derby, Derbyshire',
                        'peterborough': 'Peterborough, Cambridgeshire',
                        'blackpool': 'Blackpool, Lancashire',
                        'wakefield': 'Castleford, Wakefield',
                        'manchester': 'Wilmslow, Manchester',
                        'newcastle': 'Gateshead, Newcastle',
                        'sunderland': 'Sunderland, Tyne and Wear',
                        'knutsford': 'Knutsford, Cheshire',
                        'sthelens': 'St Helens, Merseyside',
                        'epsom': 'Epsom, London',
                        'lakedistrict': 'Kendal, Lake District'
                    }
                    location_text = location_display.get(location.lower(), location)
                    
                    button_html = f'''
                    <div class="hotel-card">
                        <h4 class="hotel-location">{location_text}</h4>
                        <h3 class="hotel-name">{hotel_name}</h3>
                        <a href="{url}" class="book-now-btn" target="_blank" rel="noopener">BOOK NOW</a>
                    </div>
                    '''
                    
                    # Add the button after the hotel mention with more precise replacement
                    answer = re.sub(pattern, f"{hotel_name}\n{button_html}", answer, count=1)
            
            # Limit the size of the response to prevent large payloads
            if len(answer) > 8000:
                logger.warning("Response too long (%d chars), truncating", len(answer))
                answer = answer[:8000] + "... [Response truncated due to length]"
                
            logger.info("Generated answer: %s", answer[:100] + "..." if len(answer) > 100 else answer)

            # Process the answer to ensure HTML is properly handled
            processed_answer = Markup(answer)

            return jsonify({"answer": processed_answer})
        except Exception as e:
            error_msg = f"Error with OpenAI API: {str(e)}"
            logger.error(error_msg)
            
            # Try with an even simpler request as fallback
            try:
                logger.info("Trying fallback request to OpenAI")
                fallback_response = client.chat.completions.create(
                    model="gpt-4o",  # Using full GPT-4o model for fallback as well
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant for AG Hotels."},
                        {"role": "user", "content": "Tell me about hotel accommodations."}
                    ],
                    temperature=0.7,
                    max_tokens=150
                )
                
                if fallback_response and fallback_response.choices and len(fallback_response.choices) > 0:
                    logger.info("Fallback successful, API is working")
                    return jsonify({
                        "error": "The original request failed, but our API connection is working. Please try a simpler question.",
                        "answer": "I apologize, but I had trouble processing your specific request. Could you please try asking a simpler or more concise question?"
                    }), 200
                else:
                    logger.error("Fallback request also failed")
                    return jsonify({
                        "error": error_msg,
                        "answer": "I apologize, but our AI service is currently experiencing issues. Please try again later."
                    }), 500
            except Exception as fallback_error:
                logger.error(f"Fallback request failed: {str(fallback_error)}")
                return jsonify({
                    "error": error_msg,
                    "answer": "I apologize, but our AI service is currently experiencing issues. Please try again later."
                }), 500
    except Exception as e:
        error_msg = f"Error processing request: {str(e)}"
        logger.error(error_msg)
        return jsonify({
            "error": error_msg,
            "answer": "I apologize, but I encountered an error processing your request. Please try asking your question again."
        }), 500

@app.route('/rate', methods=['POST'])
def rate_response():
    try:
        data = request.json
        if not data or 'helpful' not in data or 'message' not in data:
            return jsonify({"error": "Invalid rating data"}), 400

        # Log the rating
        rating_type = "HELPFUL" if data['helpful'] else "NOT_HELPFUL"
        ratings_logger.info(f"RATING: {rating_type} - Message: {data['message'][:100]}...")
        
        return jsonify({"status": "success"})
    except Exception as e:
        logger.error(f"Error processing rating: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=8084) 