from openai import OpenAI
from youtube_transcript_api import YouTubeTranscriptApi
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
import streamlit as st
import re

api_key = st.secrets["openai_api_key"]

llm = init_chat_model("gpt-4o-mini", model_provider="openai", temperature=0, api_key=api_key)

client = OpenAI(api_key=api_key)

def convert_youtube_url(url: str) -> str:
    # Check if the URL is already in the full format
    if re.match(r"https://www\.youtube\.com/watch\?v=", url):
        return url
    
    # Match and convert shortened youtu.be links
    match = re.match(r"https://youtu\.be/([\w-]+)", url)
    if match:
        video_id = match.group(1)
        return f"https://www.youtube.com/watch?v={video_id}"
    
    # If URL doesn't match known formats, return as is
    return url

def get_transcript(video_url):
    try:
        # Handle short youtube URLs
        video_url = convert_youtube_url(video_url).strip()
        
        # Extract video ID from URL
        video_id = video_url.split("v=")[-1].split("&")[0]
        
        # Get transcript
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        
        # Combine text
        full_transcript = "\n".join([entry["text"] for entry in transcript])
        
        return full_transcript
    except Exception as e:
        return f"Error: {str(e)}"

def generate_functions(strategy_desc):
    """Uses GPT to create Python functions for computing indicators and generating alerts."""

    system_template = """
    You are an expert algorithmic trader and software engineer specializing in developing robust, production-ready trading strategies.
    You have deep knowledge in technical analysis, risk management, and structured data extraction.
    When generating code, use clear, modular, and well-commented Python that leverages relevant libraries (e.g., Pandas, NumPy, TA-Lib) 
    and best practices for error handling and testing.
    Ensure your solutions extract structured trading signals from market data and implement strategy logic efficiently.
    """

    user_template = """
    Given the following trading strategy description:

    {strategy_desc}

    Please generate two Python functions:

    1️⃣ **`calculate_indicators(df: pd.DataFrame) -> pd.DataFrame`**  
       - Takes a Pandas DataFrame (`df`) of market data with columns: `Close`, `High`, `Low`, `Volume`, `timestamp`.  
       - Computes **technical indicators** relevant to the strategy, such as moving averages, RSI, MACD, and others as needed.  
       - Returns the updated DataFrame with these computed indicators.

    2️⃣ **`generate_trading_signal(df: pd.DataFrame) -> dict`**  
       - Takes the updated `df` (with computed indicators) and generates a trading signal.  
       - Determines the **trend** based on moving average crossovers.  
       - Uses **MACD & RSI** for confirmation before deciding to `BUY`, `SELL`, or `HOLD`.  
       - Returns a structured alert as **valid JSON**, following this exact format:
         ```json
         {{
             "Trend": "Uptrend" | "Downtrend" | "Sideways",
             "RSI": float,
             "MACD": "Bullish" | "Bearish",
             "Volume": int,
             "Timestamp": str,
             "ACTION": "BUY" | "SELL" | "HOLD"
         }}
         ```

    **Additional Requirements:**  
    - Use Python best practices with Pandas and `ta` library.  
    - Ensure efficient calculations and error handling.  
    - Functions should be modular and production-ready.
    
    Return the code ONLY, no explanations.
    """

    # Create a ChatPromptTemplate properly
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", system_template),
        ("user", user_template)
    ])

    # Correct way to invoke the template
    prompt = prompt_template.format_messages(strategy_desc=strategy_desc)

    response = llm.invoke(prompt)
    
    return response.content

def save_transcript_to_file(transcript_text: str, filename: str) -> None:
    with open(filename, "w") as file:
        file.write(transcript_text)
    st.success(f"Transcript saved to {filename}")

def split_text_into_chunks(text: str) -> list:
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=0,
        length_function=len,
        is_separator_regex=False,
    )
    texts = text_splitter.create_documents([text])
    return texts

def summarize_chunk(chunk):
    prompt = ChatPromptTemplate.from_template("Summarize this trading strategy ensuring that all relevant indicators mentioned are retained in summary: {context}")
    chain = create_stuff_documents_chain(llm, prompt)
    result = chain.invoke({"context": chunk})
    return result