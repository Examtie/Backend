import pdfplumber
import requests
from io import BytesIO

class CLIENT_OCR:
    def __init__(self):
        self.headers = {
            'accept': 'application/json',
            'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8,th;q=0.7',
            'cache-control': 'no-cache',
            'content-type': 'application/json',
            'github-verified-fetch': 'true',
            'pragma': 'no-cache',
            'priority': 'u=1, i',
            'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
        }

    def ocr(self, file_url: str = None, pdf_bytes: str = None) -> str:
        print(pdf_bytes)
        if pdf_bytes:
            response = pdf_bytes
            with pdfplumber.open(BytesIO(response)) as pdf:
                text = ''
                for page in pdf.pages:
                    text += page.extract_text()
        else:
            response = requests.get(file_url, headers=self.headers)

            if response.status_code != 200:
                raise Exception("Failed to download the file. Status code: {}".format(response.status_code))

            with pdfplumber.open(BytesIO(response.content)) as pdf:
                text = ''
                for page in pdf.pages:
                    text += page.extract_text()

        return text
