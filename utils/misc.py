import base64

# Custom stdout to capture tqdm output

class StdoutCapture:
    def __init__(self, queue):
        self.queue = queue
        
    def write(self, text):
        self.queue.put(text)
        
    def flush(self):
        pass


def download_zip(zip_file):
    """
    Generates a link to download the given ZIP file.
    
    Params:
    ------
    zip_file (str): File to download.
    
    Returns:
    -------
    (str): HTML anchor tag to download the ZIP file.
    """
    # Read the ZIP file as binary data
    with open(zip_file, "rb") as f:
        zip_data = f.read()

    # Encode the binary data in base64
    b64 = base64.b64encode(zip_data).decode()

    # Generate the HTML link for downloading
    dl_link = f"""
    <html>
    <head>
    <title>Start Auto Download file</title>
    <script src="https://code.jquery.com/jquery-3.2.1.min.js"></script>
    <script>
    $('<a href="data:application/zip;base64,{b64}" download="{zip_file}">')[0].click()
    </script>
    </head>
    </html>
    """
    
    return dl_link