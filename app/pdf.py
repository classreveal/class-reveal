import PyPDF2

def read_pdf(file_path):
    pdf_reader = PyPDF2.PdfFileReader(open(file_path, 'rb'))
    page_obj = pdfReader.getPage(0)
    text = page_obj.extractText()
    return text
