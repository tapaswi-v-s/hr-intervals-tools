import json
import streamlit as st
import pinecone
from tqdm import tqdm
from typing import List, Dict

class PineconeManager:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.pinecone = pinecone.Pinecone(api_key=self.api_key)
        
    def list_indexes(self) -> List[str]:
        try:
            return self.pinecone.list_indexes().names()
        except Exception as e:
            st.error(f"Connection failed: {str(e)}")
            st.stop()

    def index_exists(self, index_name: str) -> bool:
        return index_name in self.list_indexes()
    
    def connect_index(self, index_name: str):
        try:
            return self.pinecone.Index(index_name)
        except pinecone.exceptions.NotFoundException:
            st.error(f"Index '{index_name}' not found. Please create it first through Pinecone console.")
            st.stop()

def main():
    st.set_page_config(page_title="Pinecone Ingest", page_icon="💾", layout="wide")
    st.title("Pinecone DB Vector Ingestion")

    # Step 1: File and API Key Upload
    with st.container(border=True):
        st.header("Step 1: Upload Files and API Key")
        
        uploaded_files = st.file_uploader(
            "Upload JSON embedding files", 
            type="json",
            accept_multiple_files=True
        )
        
        pinecone_key = st.text_input("Pinecone API Key", type="password")
        
        if uploaded_files and pinecone_key:
            st.session_state.step1_complete = True
            st.session_state.uploaded_files = uploaded_files
            st.session_state.pinecone_key = pinecone_key
            st.success("Files and API key received. Proceed to Step 2.")

    # Step 2: Pinecone Connection
    if 'step1_complete' in st.session_state:
        with st.container(border=True):
            st.header("Step 2: Pinecone Configuration")
            
            try:
                pc = PineconeManager(st.session_state.pinecone_key)
                indexes = pc.list_indexes()
                
                if not indexes:
                    st.warning("No indexes found in your Pinecone project. Please create an index first through Pinecone console.")
                    st.stop()
                
                col1, col2 = st.columns(2)
                with col1:
                    index_name = st.selectbox(
                        "Select Pinecone index:",
                        options=indexes,
                        index=0
                    )
                with col2:
                    namespace = st.text_input("Namespace:", disabled=True, 
                                              value="SIMPLE-SPLIT-large-1024")
                
                if st.button("Connect to Pinecone"):
                    if not pc.index_exists(index_name):
                        st.error(f"Index '{index_name}' does not exist. Please create it first through Pinecone console.")
                        st.stop()
                        
                    st.session_state.pc_index = pc.connect_index(index_name)
                    st.session_state.namespace = namespace
                    st.session_state.step2_complete = True
                    st.success(f"Connected to index: {index_name}")
                    
            except Exception as e:
                st.error(f"Connection failed: {str(e)}")
                st.stop()

    # Step 3: Upsert Process
    if 'step2_complete' in st.session_state:
        with st.container(border=True):
            st.header("Step 3: Vector Upsert")
            
            if st.button("Start Upsert Process"):
                pc_index = st.session_state.pc_index
                namespace = st.session_state.namespace
                total_files = len(st.session_state.uploaded_files)
                
                progress_bar = st.progress(0)
                status = st.status("Initializing upsert process...", expanded=True)
                total_vectors = 0

                with status:
                    for i, uploaded_file in enumerate(st.session_state.uploaded_files):
                        # Update progress
                        progress = (i + 1) / total_files
                        progress_bar.progress(progress)
                        status.update(
                            label=f"Processing files... ({int(progress*100)}%)",
                            state="running"
                        )
                        
                        # Load and validate vectors
                        try:
                            data = json.load(uploaded_file)
                            if not isinstance(data, list):
                                raise ValueError("Invalid JSON format - expected array of vectors")
                                
                            # Upsert vectors
                            batch_size = 100
                            for i in tqdm(range(0, len(data), batch_size)):
                                batch = data[i:i+batch_size]
                                pc_index.upsert(
                                    vectors=batch,
                                    namespace=namespace
                                )
                            
                            total_vectors += len(data)
                            status.write(f"Processed {uploaded_file.name} ({len(data)} vectors)")
                            
                        except Exception as e:
                            status.error(f"Error in {uploaded_file.name}: {str(e)}")
                            st.stop()
                
                    # Final status
                    progress_bar.progress(100)
                    status.update(
                        label=f"Upsert completed! Total vectors: {total_vectors}",
                        state="complete",
                        expanded=False
                    )

if __name__ == "__main__":
    main()
