from gradio_client import Client, handle_file


class TyphoonOCR:
    def __init__(self):
        self.client = Client("opentyphoon/typhoon-ocr")

    def ocr(self, file_url: str) -> str:
        result = self.client.predict(
                pdf_or_image_file=handle_file(file_url),
                task_type="structure",
                page_number=1,
                api_name="/process_pdf"
        )
        print(result)
        return result

