from langchain_text_splitters import CharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Verify API key is loaded
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY not found in environment variables")

def create_hotel_chatbot():
    # Load the hotel data
    with open('hotel_data.txt', 'r') as file:
        hotel_data = file.read()

    # Split text into chunks
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    chunks = text_splitter.split_text(hotel_data)

    # Create embeddings and vector store
    embeddings = OpenAIEmbeddings(openai_api_key=api_key)
    vectorstore = FAISS.from_texts(chunks, embeddings)

    # Create memory
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True
    )

    # Create conversation chain
    qa = ConversationalRetrievalChain.from_llm(
        llm=ChatOpenAI(temperature=0.7, openai_api_key=api_key),
        retriever=vectorstore.as_retriever(),
        memory=memory
    )

    return qa

def chat_with_hotel_bot():
    qa = create_hotel_chatbot()
    
    print("Welcome to AG Hotels AI Assistant! Ask me anything about our hotels and services.")
    print("Type 'quit' to exit")
    
    while True:
        question = input("\nYou: ")
        if question.lower() == 'quit':
            break
            
        try:
            result = qa({"question": question})
            print("\nAI Assistant:", result['answer'])
        except Exception as e:
            print("\nError:", str(e))

if __name__ == "__main__":
    chat_with_hotel_bot()
