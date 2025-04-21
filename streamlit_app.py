import streamlit as st
import os
from dotenv import load_dotenv
from openai import OpenAI
import glob
import traceback
import tiktoken

# Load environment variables from .env file
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="AG Hotels Assistant",
    page_icon="🏨",
    layout="wide"
)

def num_tokens_from_string(string, model="gpt-3.5-turbo"):
    """Returns the number of tokens in a text string."""
    try:
        encoding = tiktoken.encoding_for_model(model)
        num_tokens = len(encoding.encode(string))
        return num_tokens
    except Exception as e:
        st.session_state.logs.append(f"Error calculating tokens: {str(e)}")
        # Fallback approximation: 1 token ~= 4 chars for English text
        return len(string) // 4

def load_hotel_data():
    """Load all the hotel data from text files in the data directory."""
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
                st.session_state.logs.append(f"Loaded {category} data: {len(content)} characters")
        except Exception as e:
            st.session_state.logs.append(f"Error loading {filepath}: {str(e)}")
            hotel_data[category] = ""
    
    return hotel_data

def initialize_openai_client():
    """Initialize the OpenAI client with error handling."""
    try:
        # Get API key from environment variables
        # For Streamlit Cloud, use st.secrets instead of environment variables
        api_key = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY"))
        
        if not api_key:
            st.error("OpenAI API key not found. Please set it in your .env file or Streamlit secrets.")
            st.session_state.logs.append("ERROR: OpenAI API key not found")
            return None
            
        st.session_state.logs.append(f"Initializing OpenAI client with key starting with: {api_key[:10]}...")
        return OpenAI(api_key=api_key)
    except Exception as e:
        st.error(f"Error initializing OpenAI client: {str(e)}")
        st.session_state.logs.append(f"ERROR: {str(e)}")
        return None

def extract_relevant_chunks(question, hotel_data, max_tokens=8000):
    """Extract the most relevant chunks of hotel data based on the question."""
    # Lower token count for system message, question, and formatting
    system_tokens = 500
    question_tokens = num_tokens_from_string(question)
    available_tokens = max_tokens - system_tokens - question_tokens - 500  # 500 for buffer
    
    st.session_state.logs.append(f"Available tokens for data: {available_tokens}")
    
    # Keywords from the question to help identify relevant sections
    keywords = [word.lower() for word in question.split() if len(word) > 3]
    
    # Simple relevance scoring for each category
    relevant_data = {}
    
    # Check if any hotel name is mentioned specifically
    hotel_names = ["The Crown Hotel", "Plaza Hotel", "Fortune Hotel", "The Stuart Hotel", 
                   "The Milestone Hotel", "Bluewaters Hotel", "Pinewood Hotel"]
    
    mentioned_hotels = [hotel for hotel in hotel_names if hotel.lower() in question.lower()]
    
    for category, content in hotel_data.items():
        # Split into paragraphs
        paragraphs = content.split('\n\n')
        relevant_paragraphs = []
        
        # If specific hotels are mentioned, prioritize those sections
        if mentioned_hotels:
            for hotel in mentioned_hotels:
                hotel_paragraphs = [p for p in paragraphs if hotel.lower() in p.lower()]
                relevant_paragraphs.extend(hotel_paragraphs)
        
        # Add paragraphs with keywords
        for paragraph in paragraphs:
            if any(keyword in paragraph.lower() for keyword in keywords):
                if paragraph not in relevant_paragraphs:
                    relevant_paragraphs.append(paragraph)
        
        # If we don't have enough relevant paragraphs, add some general ones
        if len(relevant_paragraphs) < 3 and len(paragraphs) > 3:
            # Add introductory paragraphs which often contain general info
            for p in paragraphs[:3]:
                if p not in relevant_paragraphs:
                    relevant_paragraphs.append(p)
        
        # Join relevant paragraphs
        relevant_content = '\n\n'.join(relevant_paragraphs)
        
        # Track token counts
        tokens = num_tokens_from_string(relevant_content)
        st.session_state.logs.append(f"{category} relevant content: {tokens} tokens")
        
        relevant_data[category] = relevant_content
    
    # Calculate total tokens
    total_tokens = sum(num_tokens_from_string(content) for content in relevant_data.values())
    
    # If we still exceed the token limit, trim the data proportionally
    if total_tokens > available_tokens:
        reduction_factor = available_tokens / total_tokens
        for category in relevant_data:
            # Simple approach: take the first X% of each content
            content = relevant_data[category]
            reduced_length = int(len(content) * reduction_factor)
            relevant_data[category] = content[:reduced_length]
            
        st.session_state.logs.append(f"Reduced data to fit token limit. Reduction factor: {reduction_factor:.2f}")
    
    return relevant_data

def ask_question(client, question, hotel_data):
    """Send a question to the OpenAI API and get a response."""
    try:
        if not client:
            return "Error: OpenAI client not initialized"
            
        st.session_state.logs.append(f"Received question: {question}")
        
        # Extract relevant chunks of data to stay within token limits
        relevant_data = extract_relevant_chunks(question, hotel_data)
        
        # Create system message with all available data
        system_message = """You are an AI assistant for AG Hotels. Your job is to provide detailed, helpful information based on the hotel data provided to you.
        
IMPORTANT INSTRUCTIONS:
1. Use ONLY the information provided in the data files to answer questions.
2. DO NOT say "this information is not available" when information exists in the data files.
3. Make sure to ALWAYS search through ALL the data before responding.
4. The location.txt file contains details about hotel rooms, suites, and amenities.
5. The weddings.txt file contains information about wedding venues and packages.
6. The hotel_data.txt file contains general information about AG Hotels.

Be thorough in searching the data for relevant information."""
        
        # Create prompt for API
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": f"""Customer question: {question}

Here is the relevant data to search through:

=== LOCATION DATA ===
{relevant_data.get('location', '')}

=== WEDDINGS DATA ===
{relevant_data.get('weddings', '')}

=== HOTEL_DATA ===
{relevant_data.get('hotel_data', '')}

Please provide a helpful, detailed answer based on the above information."""}
        ]
        
        # Estimate total tokens
        total_tokens = (
            num_tokens_from_string(system_message) +
            num_tokens_from_string(question) +
            sum(num_tokens_from_string(content) for content in relevant_data.values()) +
            100  # buffer for formatting
        )
        
        st.session_state.logs.append(f"Estimated total tokens: {total_tokens}")
        
        # Check if we're still over the limit
        if total_tokens > 15000:  # safe limit for gpt-3.5-turbo
            st.session_state.logs.append("WARNING: Still over token limit, reducing content further")
            for category in relevant_data:
                relevant_data[category] = relevant_data[category][:len(relevant_data[category])//2]
            
            # Update the message with reduced content
            messages[1]["content"] = f"""Customer question: {question}

Here is the relevant data to search through (reduced due to token limits):

=== LOCATION DATA ===
{relevant_data.get('location', '')}

=== WEDDINGS DATA ===
{relevant_data.get('weddings', '')}

=== HOTEL_DATA ===
{relevant_data.get('hotel_data', '')}

Please provide a helpful, detailed answer based on the above information."""
        
        st.session_state.logs.append("Sending request to OpenAI...")
        
        # Call OpenAI API with error handling
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Using cheaper/faster model for testing
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )
        
        # Process the response
        if not response or not response.choices or len(response.choices) == 0:
            st.session_state.logs.append("ERROR: Empty response from OpenAI")
            return "I apologize, but I didn't receive a proper response. Please try again."
            
        answer = response.choices[0].message.content
        
        if not answer or answer.strip() == "":
            st.session_state.logs.append("ERROR: Empty answer content from OpenAI")
            return "I apologize, but I'm having trouble generating a specific response. Please try again."
            
        st.session_state.logs.append(f"Generated answer: {answer[:100]}...")
        return answer
    except Exception as e:
        error_msg = f"Error with OpenAI API: {str(e)}"
        st.session_state.logs.append(f"ERROR: {error_msg}")
        st.session_state.logs.append(f"Traceback: {traceback.format_exc()}")
        return f"I apologize, but I encountered an error: {str(e)}. Please try asking your question again."

# Initialize session state for chat history and logs
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
    
if 'logs' not in st.session_state:
    st.session_state.logs = []

# Main app layout
st.title("AG Hotels Assistant")

# Initialize OpenAI client once
if 'openai_client' not in st.session_state:
    st.session_state.openai_client = initialize_openai_client()
    
# Load hotel data once
if 'hotel_data' not in st.session_state:
    st.session_state.hotel_data = load_hotel_data()

# Create two columns
col1, col2 = st.columns([2, 1])

with col1:
    # Chat interface
    st.subheader("Chat with our AI Assistant")
    
    # Display chat history
    for message in st.session_state.chat_history:
        if message["role"] == "user":
            st.write(f"**You:** {message['content']}")
        else:
            st.write(f"**Assistant:** {message['content']}")
    
    # User input
    user_question = st.text_input("Ask a question about AG Hotels:", key="user_input")
    
    if st.button("Submit"):
        if user_question:
            # Add user message to chat history
            st.session_state.chat_history.append({"role": "user", "content": user_question})
            
            # Get response from OpenAI
            response = ask_question(st.session_state.openai_client, user_question, st.session_state.hotel_data)
            
            # Add assistant message to chat history
            st.session_state.chat_history.append({"role": "assistant", "content": response})
            
            # Rerun to update the display
            st.rerun()

with col2:
    # Debug information
    st.subheader("Debug Information")
    
    if st.checkbox("Show OpenAI API Key Status"):
        # Try getting key from Streamlit secrets first, then from environment variables
        api_key = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY"))
        if api_key:
            st.success(f"API Key is set (starts with {api_key[:5]}...)")
        else:
            st.error("API Key is not set")
    
    if st.checkbox("Show Loaded Data Categories"):
        st.write("Categories loaded:")
        for category in st.session_state.hotel_data:
            st.write(f"- {category}: {len(st.session_state.hotel_data[category])} characters")
    
    if st.checkbox("Show Debug Logs"):
        st.write("Debug logs:")
        for log in st.session_state.logs:
            st.write(f"- {log}")
        
    if st.button("Clear Chat History"):
        st.session_state.chat_history = []
        st.rerun()
        
    if st.button("Clear Logs"):
        st.session_state.logs = []
        st.rerun() 