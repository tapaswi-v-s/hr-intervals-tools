import streamlit as st
import streamlit.components.v1 as components
import os
import time
import sys
import threading
import queue
import base64
from utils.scrape import Scrape
from utils.misc import StdoutCapture, download_zip

def download(file_name):
    components.html(
        download_zip(file_name),
        height=0
    )

@st.dialog("Confirmation")
def confirmation_dialog():
    st.write("Are you sure you want to proceed with scraping?")
    col1, col2 = st.columns(2)
    with col1:
        if st.button('', icon='✅'):
            st.session_state.proceed_scraping = True
            st.rerun()
    with col2:
        if st.button('',icon='❌'):
            st.session_state.proceed_scraping = False
            st.rerun()

# Main Streamlit app
def main():
    st.set_page_config(page_title="Website Scraper", page_icon="🕸️", layout="wide")
    
    st.title("Website Scraper using Firecrawl")
    st.write("This tool helps you scrape websites using Firecrawl API.")
    
    # Step 1: API Key and File Upload
    with st.container():
        st.header("Step 1: Enter API Key and Upload URL File")
        
        api_key = st.text_input("Enter your Firecrawl API Key", type="password")
        
        uploaded_file = st.file_uploader("Upload a .txt file containing URLs (one URL per line)",
                                          type="txt")
        
        if uploaded_file is not None:
            # Save the uploaded file temporarily
            file_path = "temp_urls.txt"
            with open(file_path, "w") as f:
                content = uploaded_file.getvalue().decode("utf-8")
                f.write(content)
            
            st.success(f"File uploaded successfully!")
        
        proceed = st.button("Proceed to Scraping", disabled=(not api_key or uploaded_file is None))
    
    # Step 2: Scraping Process
    if proceed:
        if "proceed_scraping" not in st.session_state \
            or st.session_state.get('proceed_scraping', False) == False:
            confirmation_dialog()

    # time.sleep(1)
    if st.session_state.get("proceed_scraping", False):
        st.header("Step 2: Scraping Websites")
        
        # Initialize the scraper
        scraper = Scrape(file_path="temp_urls.txt", api_key=api_key)
        
        # Extract URLs
        urls = scraper.extract_urls()
        st.write(f"Found {len(urls)} URLs to scrape:")
        # st.write(", ".join(urls[:5]) + ("..." if len(urls) > 5 else ""))
        
        # Create a progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Create a text area for tqdm output
        tqdm_output = st.empty()
        
        # Set up queue for capturing tqdm output
        output_queue = queue.Queue()
        original_stdout = sys.stdout
        sys.stdout = StdoutCapture(output_queue)
        
        # Run scraping in a separate thread
        def run_scraping():
            try:
                scraper.scrape_websites()
                # Signal completion
                output_queue.put("DONE")
            except Exception as e:
                output_queue.put(f"ERROR: {str(e)}")
        
        thread = threading.Thread(target=run_scraping)
        thread.start()
        
        # Update the UI with progress
        output_text = ""
        completed = False
        total_urls = len(urls)
        current_url = 0
        
        while not completed:
            try:
                # Get output from queue with timeout
                line = output_queue.get(timeout=0.1)
                
                if line.lower() == "done":
                    completed = True
                    progress_bar.progress(100)
                    status_text.success("Scraping completed successfully!")
                elif line.lower().startswith("error"):
                    status_text.error(line)
                    completed = True
                else:
                    output_text += line
                    tqdm_output.text_area("Scraping Progress", output_text, height=200, disabled=True)
                    
                    # Try to extract progress from tqdm output
                    if "%" in line:
                        try:
                            percent = int(line.split("%")[0].split("|")[-1].strip())
                            progress_bar.progress(percent/100)
                            status_text.text(f"Scraping in progress: {percent}%")
                        except:
                            pass
                    
                    # Also check for "Scraping page: X" to update progress
                    if "Scraping page:" in line:
                        try:
                            current_url = int(line.split("Scraping page:")[1].split(".")[0].strip())
                            percent = min(100, int((current_url / total_urls) * 100))
                            progress_bar.progress(percent/100)
                            status_text.text(f"Scraping in progress: {percent}% (URL {current_url} of {total_urls})")
                        except:
                            pass
                            
                    # Check for sleep message
                    if "Sleeping for" in line:
                        status_text.info(f"Pausing for rate limit: {line}")
            except queue.Empty:
                time.sleep(0.1)
                continue
        
        # Restore stdout
        sys.stdout = original_stdout
        
        if completed and not output_text.startswith("ERROR"):
            import zipfile
                
            with zipfile.ZipFile("scraped_results.zip", "w") as zipf:
                # Add JSON files
                for file in os.listdir("./json"):
                    if file.endswith('.json'):
                        zipf.write(os.path.join("./json", file))
                
                # Add MD files
                for file in os.listdir("./md"):
                    if file.endswith('.md'):
                        zipf.write(os.path.join("./md", file))
            
            download("scraped_results.zip")
            uploaded_file = None
            proceed = None
            completed = False
            st.session_state.proceed_scraping = False

                

if __name__ == "__main__":
    main()
