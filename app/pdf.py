import PyPDF2

def read_pdf(file):
    pdf_reader = PyPDF2.PdfFileReader(file)
    page_obj = pdf_reader.getPage(0)
    text = page_obj.extractText()
    return text

if __name__ == "__main__":
    with open("/tmp/uploads/rahul.pdf", "rb") as rah:
        print(read_pdf(rah))