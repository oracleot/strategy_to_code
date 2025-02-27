import streamlit as st
from apis import generate_functions, get_transcript, summarize_chunk, split_text_into_chunks

# Sidebar Layout
with st.sidebar:
    input_method = st.radio("Describe your Trading Strategy", options=["Get from YouTube Video", "Manual Strategy Description"])

    method_is_video = input_method == "Get from YouTube Video"
    
    if method_is_video:
        user_input = st.text_input(
            "Enter YouTube Video URL",
            placeholder="https://www.youtube.com/watch?v=b2QpsIdEkfk"
        )
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

**Instructions:** For mobile users, open the sidebar by clicking the icon on the top left.
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
            # Step 1: Get Strategy Description (Transcript or Manual Description)
            if method_is_video:
                status_text.info("Fetching transcript from video...")
                transcript = get_transcript(user_input)
            else:
                status_text.info("Using manual strategy description...")
                transcript = user_input
            progress_bar.progress(25)
        
        except Exception as e:
            progress_bar.empty()
            status_text.empty()
            st.error(f"An error occurred: {e}")

        try:
            # Step 2: Summarise strategy
            status_text.info("Summarizing strategy...")
            # TODO: abstract inside API -> summarize_strategy(transcript)
            chunks = split_text_into_chunks(transcript)
            summary = summarize_chunk(chunks)
            progress_bar.progress(50)
  
        except Exception as e:
            progress_bar.empty()
            status_text.empty()
            st.error(f"An error occurred: {e}")

        try:
            # Step 3: Generate Functions
            status_text.info("Generating code from strategy...")
            generated_functions = generate_functions(summary)
            progress_bar.progress(75)
  
        except Exception as e:
            progress_bar.empty()
            status_text.empty()
            st.error(f"An error occurred: {e}")

        # Finalize Progress
        status_text.info("Finalizing...")
        progress_bar.progress(100)
        status_text.empty()

        # Create Tabs for Output
        tabs = st.tabs(["Strategy Summary", "Generated Code"])

        with tabs[0]:
            st.subheader("📝 Strategy Summary")
            st.write(summary)

        with tabs[1]:
            st.subheader("💻 Generated Code")
            st.code(generated_functions, language="python")