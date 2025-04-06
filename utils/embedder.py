import os
import re
import json
import uuid
from tqdm import tqdm
from dotenv import load_dotenv
from langchain_text_splitters import MarkdownHeaderTextSplitter
from openai import OpenAI

class Embedder:
    def __init__(self, api_key):
        self.client = OpenAI(api_key=api_key)
        self.headers_to_split_on = [
            ("#", "page_title"),
            ("##", "header"),
            ("###", "header"),
            ("####", "header"),
        ]

    def process_md_files(self, uploaded_files):
        json_dir = './json'
        os.makedirs(json_dir, exist_ok=True)
        all_files = []

        for uploaded_file in tqdm(uploaded_files, desc="Processing files"):
            file_name = uploaded_file.name
            md_content = uploaded_file.getvalue().decode("utf-8").split('\n')
            url = md_content[0].strip()
            md_text = '\n'.join(md_content[1:])

            splitter = MarkdownHeaderTextSplitter(self.headers_to_split_on)
            docs = splitter.split_text(md_text)
            
            vectors = []
            for doc in docs:
                # Clean metadata and content
                page_title = re.sub(r'[#*_\-]', '', doc.metadata.get('page_title', '')).strip()
                header = re.sub(r'[#*_\-]', '', doc.metadata.get('header', '')).strip()
                text = re.sub(r'[#*_\-]', '', doc.page_content).replace('\n', ' ').strip()
                
                # Generate embedding
                doc_string = f'{page_title} | {header} | {text}'
                embedding = self.client.embeddings.create(
                    input=doc_string,
                    model="text-embedding-3-large",
                    dimensions=1024
                ).data[0].embedding
                
                # Prepare vector data
                vector = {
                    'id': str(uuid.uuid4()),
                    'metadata': {
                        'article': page_title,
                        'header': header,
                        'url': url,
                        'doc': doc_string
                    },
                    'values': embedding
                }
                vectors.append(vector)
            
            # Save to JSON
            json_path = os.path.join(json_dir, file_name.replace('.md', '.json'))
            with open(json_path, 'w') as f:
                json.dump(vectors, f)
            all_files.append(json_path)
        
        return all_files