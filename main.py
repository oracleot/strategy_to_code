import streamlit as st
from apis import get_transcript, extract_trading_strategy, generate_functions

# Sidebar Layout
with st.sidebar:
    input_method = st.radio("Describe your Trading Strategy", options=["Get from YouTube Video", "Manual Strategy Description"])

    method_is_video = input_method == "Get from YouTube Video"
    
    if method_is_video:
        video_url = st.text_input(
            "Enter YouTube Video URL",
            placeholder="https://www.youtube.com/watch?v=b2QpsIdEkfk"
        )
        user_input = video_url.strip()
    else:
        strategy_description = st.text_area(
            "Describe your Trading Strategy",
            placeholder="Enter your trading strategy details here..."
        )
        user_input = strategy_description.strip()
    
    run_button = st.button("Generate Code")

# Main Screen Layout
st.title("Strategy to Code Generator")
st.write("""
Welcome to the **Strategy to Code Generator**!

**Instructions:**
0. For mobile users, open the sidebar by clicking the icon on the top left.
1. Choose a method to describe your Trading Strategy.
2. Either enter a YouTube video URL (to extract its transcript) or type your strategy description manually.
3. Click the "Generate Code" button.
4. Navigate through the tabs to view the strategy description, structured strategy data, and generated code.
""")

if run_button:
    if not user_input:
        st.error("Please provide the required input based on your chosen method.")
    else:
        # Initialize Progress Bar
        progress_bar = st.progress(0)
        status_text = st.empty()

        try:
            # Stage 1: Get Strategy Description (Transcript or Manual Description)
            if method_is_video:
                status_text.text("Fetching transcript from video...")
                transcript = get_transcript(user_input)
            else:
                status_text.text("Using manual strategy description...")
                transcript = user_input
            progress_bar.progress(25)

            # Stage 2: Extract Structured Data
            status_text.text("Extracting structured data from strategy description...")
            strategy_data = extract_trading_strategy(transcript)
            progress_bar.progress(50)

            # Stage 3: Generate Functions
            status_text.text("Generating code...")
            generated_functions = generate_functions(strategy_data)
            progress_bar.progress(75)

            # Finalize Progress
            status_text.text("Finalizing...")
            progress_bar.progress(100)
            status_text.empty()

            # Create Tabs for Output
            tabs = st.tabs(["📝 Strategy Description", "📊 Structured Data", "💻 Generated Code"])

            with tabs[0]:
                st.subheader("Strategy Description")
                st.write(transcript)

            with tabs[1]:
                st.subheader("Structured Data")
                st.json(strategy_data)

            with tabs[2]:
                st.subheader("Generated Code")
                st.code(generated_functions, language="python")

        except Exception as e:
            progress_bar.empty()
            status_text.empty()
            st.error(f"An error occurred: {e}")