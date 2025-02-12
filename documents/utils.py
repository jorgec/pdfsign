from pypdf import PdfReader, PdfWriter


def remove_hybrid_xrefs(pdf_path, cleaned_pdf_path):
    """Rewrites a PDF to remove hybrid cross-reference tables."""
    reader = PdfReader(pdf_path)
    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    with open(cleaned_pdf_path, "wb") as output_pdf:
        writer.write(output_pdf)
