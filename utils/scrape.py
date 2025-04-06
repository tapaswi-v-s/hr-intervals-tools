from firecrawl import FirecrawlApp
import os, json, argparse
from tqdm import tqdm
import shutil

class Scrape:
    def __init__(self, file_path, api_key):
        self.api_key = api_key
        self.file_path = file_path
        self.urls = []

    def extract_urls(self):
        """Extract URLs from the file (renamed from read_urls_from_file to match the interface)"""
        try:
            with open(self.file_path, "r") as file:
                self.urls = [line.strip() for line in file if line.strip() and 
                        not line.strip().startswith(('#', '//'))]
                return self.urls
        except FileNotFoundError:
            print(f"Error: File '{self.file_path}' not found.")
            self.urls = []
            return self.urls


    def scrape_websites(self):
        counter = 1
        for url in tqdm(self.urls, desc="Scraping URLs"):
            try:
                app = FirecrawlApp(api_key=self.api_key)

                response = app.scrape_url(url=url, params={
                    'formats': ['markdown'],
                    # 'includeTags': ['article', '#main-content'] # <- For old website
                    'includeTags': ['h1.heading-2', 'div.vc_row.wpb_row.vc_row-fluid.hr-article-template.es-import']
                })

                # title = response['metadata']['ogTitle'] # <- For old website
                title = response['markdown'].split("\n")[0].replace('#','').strip()
                print(f"Scraping page: {counter}. {title}")
                title = title.replace(' ', '_').lower()
                title = ''.join(e for e in title if e.isalnum() or e == '_')

                
                try:
                    shutil.rmtree('./json')
                    shutil.rmtree('./md')
                except FileNotFoundError:
                    pass
                os.makedirs('./json', exist_ok=True)
                os.makedirs('./md', exist_ok=True)

                with open(f'./json/{title}.json', 'w') as json_file, \
                    open(f'./md/{title}.md', 'w') as md:
                    
                    md.write(f'{response["metadata"]["url"]}\n')
                    md.write(response['markdown'])
                    json.dump(response, json_file, indent=4)
                
                if counter%10 == 0:
                    print("Sleeping for 70 seconds")
                    time.sleep(70)

                counter+=1
            except Exception as e:
                print(f"Error: {e}")
                break