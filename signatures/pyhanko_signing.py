from pyhanko.sign.signers.pdf_signer import sign_pdf
from pyhanko.sign import signers
from pyhanko.sign.fields import append_signature_field
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from django.conf import settings
import os
from signatures.utils import get_user_signature_path


def sign_pdf_with_user_signature(user, pdf_path, output_path, signature_position):
    """Sign a PDF with the user's registered signature image"""

    # Get the user's signature image path
    signature_img_path = get_user_signature_path(user)
    if not signature_img_path:
        raise ValueError("No signature registered for this user.")

    with open(pdf_path, "rb") as pdf_in:
        w = IncrementalPdfFileWriter(pdf_in)

        # Append a signature field at the specified position
        append_signature_field(
            w,
            sig_field_name="Signature1",
            box=(signature_position["x"], signature_position["y"],
                 signature_position["x"] + 100, signature_position["y"] + 50),
            page=signature_position["page"]
        )

        # Load digital certificate (Modify with your certificate details)
        with open(os.path.join(settings.BASE_DIR, "certs/my_certificate.pfx"), "rb") as key_file:
            signer = signers.SimpleSigner.load_pkcs12(key_file, passphrase=b"your_password")

        # Sign the PDF and embed the signature image
        meta = signers.PdfSignatureMetadata()
        signature = signers.PdfSigner(
            signer=signer,
            signature_meta=meta,
            appearance_text_params=signers.TextParams(),  # Optional text next to signature
            stamp_style=signers.PdfStampAppearance.from_file(signature_img_path)  # Embed the image
        )

        with open(output_path, "wb") as pdf_out:
            signature.sign_pdf(w, output=pdf_out)

    return output_path
