import re
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from docx import Document
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from transformers import BartForConditionalGeneration, BartTokenizer
from concurrent.futures import ThreadPoolExecutor
import torch
import logging

app = Flask(__name__)
CORS(app)

# Inisialisasi model dan tokenizer BART
model_name = "sshleifer/distilbart-cnn-12-6"
device = "cuda" if torch.cuda.is_available() else "cpu"
model = BartForConditionalGeneration.from_pretrained(model_name).to(device)
tokenizer = BartTokenizer.from_pretrained(model_name)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def remove_parentheses(text):
    """Menghapus teks dalam tanda kurung."""
    return re.sub(r"\(.*?\)", "", text)


def capitalize_text(text):
    """Mengkapitalisasi setiap kata dalam teks."""
    return " ".join(word.capitalize() for word in text.split())


def extract_universitas(text):
    """Mengambil bagian teks yang dimulai dari kata 'INSTITUT' atau 'UNIVERSITAS'."""
    for keyword in ["INSTITUT", "UNIVERSITAS"]:
        index = text.upper().find(keyword)
        if index != -1:
            return text[index:].strip()
    return ""


def extract_asal_kota(text):
    """Mengambil bagian teks yang mengandung nama kota di Jawa Barat dan menambahkan ', Indonesia'."""
    kota_keywords = [
        "BOGOR",
        "BANDUNG",
        "BEKASI",
        "DEPOK",
        "CIMAHI",
        "SUKABUMI",
        "CIREBON",
        "TASIKMALAYA",
        "BANJAR",
        "KARAWANG",
    ]
    for keyword in kota_keywords:
        if keyword in text.upper():
            return keyword.capitalize() + ", Indonesia"
    return ""


def summarize_text(text, min_length=200, max_length=250):
    inputs = tokenizer.encode(
        "summarize: " + text, return_tensors="pt", max_length=1024, truncation=True
    )
    inputs = inputs.to(device)
    outputs = model.generate(
        inputs,
        max_length=max_length,
        min_length=min_length,
        length_penalty=2.0,
        num_beams=4,
        early_stopping=True,
    )
    summary = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return summary


def truncate_text(text, word_limit=200):
    words = text.split()
    if len(words) > word_limit:
        return " ".join(words[:word_limit])
    return text


@app.route("/convert", methods=["POST"])
def convert_to_journal():
    if "file" not in request.files:
        return jsonify({"error": "Tidak ada bagian file"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Tidak ada file yang dipilih"}), 400

    try:
        # Membaca file DOCX
        doc = Document(file)

        # Mengumpulkan judul, penulis, program studi, universitas, asal kota, abstrak, dan keywords
        title_lines = []
        author = ""
        program_studi = ""
        universitas = ""
        asal_kota = ""
        abstract = ""
        pendahuluan = ""
        metode_penelitian = ""
        keywords = ""
        found_author = False
        found_abstract = False
        found_pendahuluan = False
        found_metode_penelitian = False

        author_keywords = ["Oleh", "OLEH", "Disusun oleh", "Ditulis oleh"]
        program_studi_keywords = ["PROGRAM STUDI"]
        universitas_keywords = ["INSTITUT", "UNIVERSITAS", "POLITEKNIK"]
        abstract_keyword = "ABSTRACT"
        pendahuluan_keyword = "PENDAHULUAN"
        metode_penelitian_keyword = "METODE PENELITIAN"
        keywords_keyword = "Keywords:"

        for paragraph in doc.paragraphs:
            text = paragraph.text.strip()

            if text:
                text = remove_parentheses(text)  # Hapus teks dalam kurung
                if not title_lines and not found_abstract:
                    title_lines.append(text)
                elif len(title_lines) < 2 and not found_abstract:
                    title_lines.append(text)
                elif not author and any(keyword in text for keyword in author_keywords):
                    author = text.split(":")[-1].strip()
                    found_author = True
                elif (
                    found_author
                    and not author
                    and not any(
                        keyword in text
                        for keyword in program_studi_keywords + universitas_keywords
                    )
                ):
                    author = text.strip()
                    found_author = False
                elif any(keyword in text for keyword in program_studi_keywords):
                    if "FAKULTAS" in text.upper():
                        parts = text.split("FAKULTAS")
                        program_studi = parts[0].replace("SARJANA", "").strip()
                        universitas = extract_universitas("FAKULTAS" + parts[1])
                    else:
                        program_studi = text.replace("SARJANA", "").strip()
                elif any(keyword in text for keyword in universitas_keywords):
                    universitas = text.strip()
                if not asal_kota:
                    kota_dari_paragraf = extract_asal_kota(text)
                    if kota_dari_paragraf:
                        asal_kota = kota_dari_paragraf
                if abstract_keyword in text.upper():
                    found_abstract = True
                elif found_abstract and not found_pendahuluan:
                    if pendahuluan_keyword in text.upper():
                        found_pendahuluan = True
                    elif keywords_keyword in text:
                        keywords = text.split(keywords_keyword, 1)[1].strip()
                        break
                    elif (
                        "NPM" not in text.upper() and "SUPERVISION" not in text.upper()
                    ):
                        abstract += " " + text
                elif found_pendahuluan and not found_metode_penelitian:
                    if metode_penelitian_keyword in text.upper():
                        found_metode_penelitian = True
                    else:
                        pendahuluan += " " + text
                elif found_metode_penelitian:
                    if keywords_keyword in text:
                        keywords = text.split(keywords_keyword, 1)[1].strip()
                        break
                    else:
                        metode_penelitian += " " + text

        # Jika tidak ditemukan judul
        if not title_lines:
            return jsonify({"error": "Judul tidak ditemukan dalam dokumen"}), 404

        # Potong teks abstrak, pendahuluan, dan metode penelitian ke 200 kata pertama
        abstract = truncate_text(abstract)
        pendahuluan = truncate_text(pendahuluan)
        metode_penelitian = truncate_text(metode_penelitian)

        # Meringkas teks menggunakan pemrosesan paralel
        with ThreadPoolExecutor() as executor:
            abstract_future = executor.submit(summarize_text, abstract)
            pendahuluan_future = executor.submit(summarize_text, pendahuluan)
            metode_penelitian_future = executor.submit(
                summarize_text, metode_penelitian
            )

            abstract = abstract_future.result()
            pendahuluan = pendahuluan_future.result()
            metode_penelitian = metode_penelitian_future.result()

        # Data yang akan dikirimkan kembali ke frontend
        data = {
            "title": "\n".join(title_lines).upper(),
            "author": capitalize_text(author),
            "program_studi": capitalize_text(program_studi),
            "universitas": capitalize_text(universitas),
            "asal_kota": capitalize_text(asal_kota),
            "abstract": abstract.strip(),
            "pendahuluan": pendahuluan.strip(),
            "metode_penelitian": metode_penelitian.strip(),
            "keywords": keywords.strip(),
        }

        # Proses konversi ke PDF menggunakan ReportLab
        pdf_data = generate_pdf(data)

        # Mengirimkan respons dengan file PDF
        return send_file(
            BytesIO(pdf_data),
            mimetype="application/pdf",
            as_attachment=True,
            download_name="converted.pdf",
        )

    except Exception as e:
        logger.error(f"Error during conversion: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500


def generate_pdf(data):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)

    # Mengatur margin dan area kerja
    margin_left = 4 * cm
    margin_right = 3 * cm
    margin_top = 3 * cm
    margin_bottom = 3 * cm

    # Lebar area kerja yang tersedia
    width = letter[0] - margin_left - margin_right

    def draw_wrapped_text_centered(text, y, font_name="Times-Roman", font_size=12):
        pdf.setFont(font_name, font_size)
        lines = []
        words = text.split()
        current_line = ""

        for word in words:
            if pdf.stringWidth(current_line + " " + word, font_name, font_size) < width:
                current_line += " " + word if current_line else word
            else:
                lines.append(current_line)
                current_line = word

        lines.append(current_line)

        for line in lines:
            if y < margin_bottom:
                pdf.showPage()
                y = letter[1] - margin_top

            text_width = pdf.stringWidth(line, font_name, font_size)
            x = (letter[0] - text_width) / 2
            pdf.drawString(x, y, line)
            y -= font_size * 1.5

        return y

    def draw_wrapped_text_justified(text, y, font_name="Times-Roman", font_size=12):
        pdf.setFont(font_name, font_size)
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            test_line = " ".join(current_line + [word])
            if pdf.stringWidth(test_line, font_name, font_size) < width:
                current_line.append(word)
            else:
                lines.append(" ".join(current_line))
                current_line = [word]

        lines.append(" ".join(current_line))

        for line in lines:
            if y < margin_bottom:
                pdf.showPage()
                y = letter[1] - margin_top

            if line == lines[-1]:
                pdf.drawString(margin_left, y, line)
            else:
                line_words = line.split()
                if len(line_words) > 1:
                    total_spaces = len(line_words) - 1
                    line_width = pdf.stringWidth(line, font_name, font_size)
                    space_width = pdf.stringWidth(" ", font_name, font_size)
                    extra_space = (width - line_width) / total_spaces
                    x = margin_left

                    for word in line_words[:-1]:
                        pdf.drawString(x, y, word)
                        x += (
                            pdf.stringWidth(word, font_name, font_size)
                            + space_width
                            + extra_space
                        )
                    pdf.drawString(x, y, line_words[-1])
                else:
                    pdf.drawString(margin_left, y, line)

            y -= font_size * 1.5

        return y

    def draw_keywords_justified(
        keywords,
        y,
        font_name_bold="Times-BoldItalic",
        font_name_regular="Times-Roman",
        font_size=12,
    ):
        combined_text = "Keywords: " + keywords
        pdf.setFont(font_name_regular, font_size)

        words = combined_text.split()
        lines = []
        current_line = []

        for word in words:
            test_line = " ".join(current_line + [word])
            if pdf.stringWidth(test_line, font_name_regular, font_size) < width:
                current_line.append(word)
            else:
                lines.append(" ".join(current_line))
                current_line = [word]

        lines.append(" ".join(current_line))

        for line in lines:
            if y < margin_bottom:
                pdf.showPage()
                y = letter[1] - margin_top

            if line == lines[-1]:
                pdf.drawString(margin_left, y, line)
            else:
                line_words = line.split()
                if len(line_words) > 1:
                    total_spaces = len(line_words) - 1
                    line_width = pdf.stringWidth(line, font_name_regular, font_size)
                    space_width = pdf.stringWidth(" ", font_name_regular, font_size)
                    extra_space = (width - line_width) / total_spaces
                    x = margin_left

                    for word in line_words[:-1]:
                        if word == "Keywords:":
                            pdf.setFont(font_name_bold, font_size)
                        else:
                            pdf.setFont(font_name_regular, font_size)
                        pdf.drawString(x, y, word)
                        x += (
                            pdf.stringWidth(word, font_name_regular, font_size)
                            + space_width
                            + extra_space
                        )
                    pdf.drawString(x, y, line_words[-1])
                else:
                    if line == "Keywords:":
                        pdf.setFont(font_name_bold, font_size)
                    else:
                        pdf.setFont(font_name_regular, font_size)
                    pdf.drawString(margin_left, y, line)

            y -= font_size * 1.5

        return y

    # Posisi y untuk judul, mengatur agar berada di bagian paling atas sebelum header
    y = letter[1] - margin_top

    # Menulis judul ke file PDF
    y = draw_wrapped_text_centered(data["title"], y, "Times-Bold", 14)

    # Menulis nama penulis
    y -= 14 * 1.5
    y = draw_wrapped_text_centered(data["author"], y, "Times-Roman", 11)

    # Menulis program studi dan universitas di baris yang sama tanpa jarak tambahan
    combined_line = f"{data['program_studi']}, {data['universitas']}"
    y = draw_wrapped_text_centered(combined_line, y, "Times-Italic", 11)

    # Menulis asal kota tanpa jarak tambahan
    y = draw_wrapped_text_centered(data["asal_kota"], y, "Times-Roman", 11)

    # Menulis abstrak dengan format yang sesuai
    y -= 20
    y = draw_wrapped_text_justified("ABSTRACT", y, "Times-BoldItalic", 12)
    y = draw_wrapped_text_justified(data["abstract"], y, "Times-Italic", 11)

    if data["keywords"]:
        y -= 10
        y = draw_keywords_justified(
            data["keywords"], y, "Times-BoldItalic", "Times-Italic", 11
        )

    # Menulis sub judul dengan format yang sesuai
    sub_titles = [
        "PENDAHULUAN",
        "TINJAUAN PUSTAKA",
        "METODOLOGI PENELITIAN",
        "HASIL DAN PEMBAHASAN",
        "KESIMPULAN DAN SARAN",
        "DAFTAR PUSTAKA",
    ]
    for sub_title in sub_titles:
        y -= 20
        y = draw_wrapped_text_justified(sub_title, y, "Times-Bold", 12)

    pdf.save()

    pdf_data = buffer.getvalue()
    buffer.close()
    return pdf_data


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
