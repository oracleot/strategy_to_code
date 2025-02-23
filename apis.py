import streamlit as st
import json
from openai import OpenAI
from youtube_transcript_api import YouTubeTranscriptApi

api_key = st.secrets["openai_api_key"]

client = OpenAI(api_key=api_key)

def get_transcript(video_url):
    try:
        # Extract video ID from URL
        video_id = video_url.split("v=")[-1].split("&")[0]
        
        # Get transcript
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        
        # Combine text
        full_transcript = "\n".join([entry["text"] for entry in transcript])
        
        return full_transcript
    except Exception as e:
        return f"Error: {str(e)}"

def extract_trading_strategy(transcript_text):
    """Uses GPT-4 to extract structured trading strategy details from a transcript."""
    prompt = f"""
    Extract the trading strategy details from the following transcript and return it in structured JSON format.
    The JSON should include:
    - "indicators": List of indicators used (e.g., RSI, MACD, EMA)
    - "parameters": Parameters for each indicator (e.g., RSI period: 14, EMA short: 9, EMA long: 50)
    - "conditions": Entry and exit conditions for trades (e.g., RSI crossing 50 upwards means buy)
    - "notes": Any additional relevant information.

    Rules:
    - Use "ma" for moving averages (with period as a subkey).
    - Use standard indicator names (e.g., "rsi", "macd") in lowercase.
    - All keys should be in lowercase.
    - Provide a descriptive explanation in the "function" field for each indicator.

    Transcript:
    {transcript_text}
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            store=True,
            messages=[
                {"role": "system", "content": "You are an expert in trading strategies and structured data extraction."},
                {"role": "user", "content": prompt}
            ]
        )
        result = response.choices[0].message.content.strip()
        # Optionally, validate the JSON
        json.loads(result)
    except Exception as e:
        raise RuntimeError("Failed to extract trading strategy details") from e

    return result

def generate_functions(strategy_data):
    """Uses GPT to create Python functions for computing indicators and generating alerts."""
    prompt = f"""
    Given the following strategy data: {strategy_data}, can you create two Python functions?

    1. A `compute_indicators` function that takes a DataFrame (`df`) of crypto data (from another `extract_crypto_data` function) and computes the indicators as specified in the `indicators` section of the strategy. The function should return the updated DataFrame with the computed indicators.

    2. A `generate_alert` function that takes the updated `df` (with computed indicators) and generates an alert signal that guides traders to take an action (either 'Buy', 'Sell', or 'Hold') based on the conditions defined in the `conditions` section of the strategy.

    Below is an example of similar functions that should help guide the output:

    ```python
    def get_crypto_data(symbol="AAVEUSDT", interval="1m", limit=200):
        url = f"https://api.binance.com/api/v3/klines?symbol={{symbol}}&interval={{interval}}&limit={{limit}}"
        response = requests.get(url).json()
        df = pd.DataFrame(response, columns=["timestamp", "open", "high", "low", "close", "volume", "close_time", "quote_asset_volume", "trades", "taker_buy_base", "taker_buy_quote", "ignore"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df["close"] = df["close"].astype(float)
        df["volume"] = df["volume"].astype(float)
        return df[["timestamp", "close", "volume"]]

    def compute_indicators(df):
        df["EMA_9"] = EMAIndicator(df["close"], window=9).ema_indicator()
        df["EMA_50"] = EMAIndicator(df["close"], window=50).ema_indicator()
        
        rsi = RSIIndicator(df["close"], window=7)  # Reduced window for scalping
        df["RSI"] = rsi.rsi()

        macd = MACD(df["close"], window_slow=13, window_fast=5, window_sign=9)  # More sensitive MACD
        df["MACD"] = macd.macd()
        df["Signal"] = macd.macd_signal()

        df["Trend"] = df["EMA_9"] > df["EMA_50"]  # EMA-based trend detection
        df["Trend"] = df["Trend"].apply(lambda x: "Up" if x else "Down")

        df["Avg_Volume"] = df["volume"].rolling(window=20).mean()
        
        return df

    def generate_alert():
        df = get_crypto_data()
        df = compute_indicators(df)
        latest = df.iloc[-2]  # Use previous candle for more accurate decisions

        action = "Hold"
        if (latest["Trend"] == "Down" and latest["MACD"] < latest["Signal"] and 
            latest["RSI"] < 40 and latest["volume"] > latest["Avg_Volume"] * 1.2):  # Volume spike filter
            action = "Sell"
        elif (latest["Trend"] == "Up" and latest["MACD"] > latest["Signal"] and 
            latest["RSI"] > 60 and latest["volume"] > latest["Avg_Volume"] * 1.2):
            action = "Buy"

        alert = {{
            "Trend": latest["Trend"],
            "RSI": round(latest["RSI"], 2),
            "MACD": "Bullish" if latest["MACD"] > latest["Signal"] else "Bearish",
            "Volume": latest["volume"],
            "Timestamp": str(latest["timestamp"]),
            "ACTION": action
        }}
        
        return alert
    ```
    Ensure that the compute_indicators function can dynamically handle different types of indicators (RSI, MACD, Moving Averages, etc.) and compute the necessary values based on the strategy data. Also, the generate_alert function should interpret the conditions provided and return the appropriate action. Also, stick to the functions generated, instructions on how to install. Avoid other unnecessary outputs or explanations.

    The strategy data may look like this:
    ```json
    {{
        "indicators": [
            {{
                "rsi": {{
                    "name": "Relative Strength Index",
                    "function": "Measures the magnitude of recent price changes to evaluate overbought or oversold conditions.",
                    "parameters": {{
                        "period": 14
                    }}
                }}
            }},
            {{
                "macd": {{
                    "name": "MACD",
                    "function": "Tracks the difference between a fast and slow exponential moving average, often used to identify momentum shifts.",
                    "parameters": {{
                        "window_slow": 26,
                        "window_fast": 12,
                        "window_sign": 9
                    }}
                }}
            }}
        ],
        "conditions": [
            {{
                "entry": {{
                    "condition": "If the RSI is below 30, and the MACD histogram is above the signal line, consider it as a buying signal."
                }},
                "exit": {{
                    "condition": "If the RSI exceeds 70, or the MACD crosses below the signal line, consider it a selling signal."
                }}
            }}
        ],
        "notes": "Ensure that indicators are used in combination rather than relying on a single indicator for entry/exit."
    }}
    ```
    """

    response = client.chat.completions.create(
        model="gpt-4",
        store=True,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert algorithmic trader and software engineer specializing in developing robust, production-ready trading strategies. "
                    "You have deep knowledge in technical analysis, risk management, and structured data extraction. "
                    "When generating code, use clear, modular, and well-commented Python that leverages relevant libraries (e.g., Pandas, NumPy, TA-Lib) and best practices for error handling and testing. "
                    "Ensure your solutions extract structured trading signals from market data and implement strategy logic efficiently."
                )
            },
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content