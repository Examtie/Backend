from ai_runner.PDFExtrack import CLIENT_OCR

# Read your PDF file into bytes
with open("math-posn-68.pdf", "rb") as f:
    pdf_bytes = f.read()

# Instantiate OCR client
x = CLIENT_OCR()

# Run OCR on the PDF bytes
result = x.ocr(pdf_bytes=pdf_bytes)

# Print result or process it
print(result)
