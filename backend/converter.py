from docx import Document
from fpdf import FPDF
import os
import zipfile
from werkzeug.utils import secure_filename


def convert_to_journal(file):
    input_filename = secure_filename(file.filename)
    file.save(input_filename)

    try:
        doc = Document(input_filename)
    except zipfile.BadZipFile:
        os.remove(input_filename)
        raise zipfile.BadZipFile("The uploaded file is not a valid DOCX file.")

    journal_text = ""
    for para in doc.paragraphs:
        journal_text += para.text + "\n"

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.set_auto_page_break(auto=True, margin=15)

    try:
        pdf.multi_cell(
            0, 10, journal_text.encode("latin-1", "replace").decode("latin-1")
        )
    except UnicodeEncodeError:
        os.remove(input_filename)
        raise UnicodeEncodeError("Error encoding the text to PDF.")

    output_filename = "output.pdf"
    output_path = os.path.join(os.getcwd(), output_filename)
    pdf.output(output_path)

    os.remove(input_filename)

    return output_path
