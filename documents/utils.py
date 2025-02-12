from pypdf import PdfReader, PdfWriter

import qrcode
import fitz  # PyMuPDF
import os
from PIL import Image  # ***Import Image from PIL***


def generate_qr_code(data, output_path):
    """Generates a QR code from the given data and saves it to the specified path."""

    qr = qrcode.QRCode(
        version=None,  # Let qrcode decide the version
        error_correction=qrcode.constants.ERROR_CORRECT_L,  # Adjust error correction as needed
        box_size=10,  # Adjust box size as needed
        border=4,  # Adjust border as needed
    )
    qr.add_data(data)
    qr.make(fit=True)  # Make the QR code fit the data

    img = qr.make_image(fill_color="black", back_color="white")  # Customize colors
    img.save(output_path)
    return output_path


def stamp_pdf_with_qr(qr_code_path, pdf_path, output_path):
    """Stamps a PDF file with a QR code on the lower right corner of the first page."""

    try:
        doc = fitz.open(pdf_path)
        page = doc[0]  # Get the first page

        # Get QR code image dimensions
        qr_img = Image.open(qr_code_path)  # PIL Image
        qr_width, qr_height = qr_img.size

        qr_width = qr_width // 4
        qr_height = qr_height // 4

        # PDF page dimensions
        page_width = page.rect.width
        page_height = page.rect.height

        # Calculate QR code position (lower right corner with some margin)
        margin = 20  # Adjust margin as needed
        x = page_width - qr_width - margin
        y = page_height - qr_height - margin

        rect = fitz.Rect(x, y, x + qr_width, y + qr_height)

        # Insert QR code
        page.insert_image(rect, filename=qr_code_path)

        doc.save(output_path, garbage=4, clean=True)  # Overwrite the PDF, and clean the PDF
        doc.close()

    except fitz.FileNotFoundError:
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    except Exception as e:
        raise Exception(f"An error occurred: {e}")


def remove_hybrid_xrefs(pdf_path, cleaned_pdf_path):
    """Rewrites a PDF to remove hybrid cross-reference tables."""
    reader = PdfReader(pdf_path)
    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    with open(cleaned_pdf_path, "wb") as output_pdf:
        writer.write(output_pdf)
