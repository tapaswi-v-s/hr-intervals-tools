import os
import streamlit as st
from zipfile import ZipFile
from utils.embedder import Embedder

def create_zip(json_files):
    zip_path = "embeddings.zip"
    with ZipFile(zip_path, 'w') as zipf:
        for file in json_files:
            zipf.write(file, os.path.basename(file))
    return zip_path

def main():
    st.set_page_config(page_title="MD Embedder", page_icon="📄", layout="wide")
    st.title("Markdown File Embedding Pipeline")

    # Step 1: File and API Key Upload
    with st.container(border=True):
        st.header("Step 1: Upload Files and API Key")
        
        uploaded_files = st.file_uploader(
            "Upload Markdown files", 
            type="md",
            accept_multiple_files=True
        )
        
        api_key = st.text_input("OpenAI API Key", type="password")
        
        if uploaded_files and api_key:
            st.session_state.step1_complete = True
            st.success("Files and API key received. Proceed to Step 2.")

    # Step 2: Embedding Process        
    if 'step1_complete' in st.session_state:
        with st.container(border=True):
            st.header("Step 2: Generate Embeddings")
            
            if st.button("Start Embedding"):
                if not api_key:
                    st.error("Please enter your OpenAI API key")
                    return
                
                embedder = Embedder(api_key)
                progress_bar = st.progress(0)
                status = st.status("Initializing embedding process...", expanded=True)
                
                try:
                    with status:
                        json_files = []
                        total_files = len(uploaded_files)
                        
                        for i, file in enumerate(uploaded_files):
                            # Calculate progress percentage
                            progress_percent = int((i + 1) / total_files * 100)
                            progress_bar.progress(progress_percent)
                            
                            # Update status with current file and percentage
                            status.update(
                                label=f"Processing files... ({progress_percent}%)",
                                state="running",
                                expanded=True
                            )
                            status.write(f"Current file: {file.name}")
                            
                            # Process the file
                            json_files += embedder.process_md_files([file])
                        
                        # Final completion message
                        progress_bar.progress(100)
                        status.update(
                            label="Embedding completed successfully!",
                            state="complete",
                            expanded=False
                        )
                        
                        # Create ZIP file
                        zip_path = create_zip(json_files)
                        st.session_state.zip_path = zip_path
                        st.session_state.embedding_done = True
                        
                except Exception as e:
                    st.error(f"Error during embedding: {str(e)}")
                    return

        # Download Section
        if 'embedding_done' in st.session_state:
            with st.container(border=True):
                st.header("Download Results")
                
                with open(st.session_state.zip_path, "rb") as f:
                    st.download_button(
                        label="Download Embeddings ZIP",
                        data=f,
                        file_name="embeddings.zip",
                        mime="application/zip"
                    )

if __name__ == "__main__":
    main()
