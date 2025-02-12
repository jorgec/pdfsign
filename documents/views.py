import json
import json
import os

from PIL import Image
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models.aggregates import Count
from django.http import JsonResponse
from django.http.response import HttpResponseRedirect
from django.shortcuts import redirect
from django.shortcuts import render, get_object_or_404
from django.views import View
from django.views.generic import ListView
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView
from pikepdf import Pdf
from pyhanko.pdf_utils.images import PdfImage
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.sign import signers
from pyhanko.sign.fields import SigFieldSpec, append_signature_field
from pyhanko.sign.signers.pdf_signer import PdfSigner, PdfSignatureMetadata
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter

from accounts.models import Account
from signatures.utils import get_user_signature_path
from .forms import DocumentUploadForm
from .models import Document, SignatureField
from .utils import remove_hybrid_xrefs


class UploadDocumentView(LoginRequiredMixin, FormView):
    template_name = "documents/upload_document.html"
    form_class = DocumentUploadForm

    def form_valid(self, form):
        # 1. Save the Document with the uploaded file
        document = form.save(commit=False)
        document.owner = self.request.user
        document.save()  # Now the file is on disk

        # 2. Get the path of the uploaded PDF
        pdf_path = document.file.path
        remove_hybrid_xrefs(pdf_path, pdf_path)

        # 3. Re-save the PDF with pikepdf to remove hybrid xrefs
        #    or other incompatible features
        try:
            with Pdf.open(pdf_path, allow_overwriting_input=True) as pdf:
                # Overwrites the same file in place
                pdf.save(pdf_path)
        except Exception as e:
            # Optionally handle errors if pikepdf fails
            # e.g. corrupt PDF, permission errors, etc.
            print(f"Error rewriting PDF with pikepdf: {e}")

        # 4. Redirect to "assign_signatures"
        return redirect("assign_signatures", pk=document.pk)


class DocumentListView(LoginRequiredMixin, ListView):
    model = Document
    template_name = "documents/document_list.html"
    context_object_name = "documents"

    def get_queryset(self):
        return Document.objects.filter(owner=self.request.user)


class DeleteDocumentView(LoginRequiredMixin, View):
    """
    Allows a logged-in user to delete their own documents.
    """

    def get(self, request, pk):
        document = get_object_or_404(Document, pk=pk)

        # Ensure only the owner can delete the document
        if document.owner != request.user:
            raise PermissionDenied

        try:
            # Remove the file from the filesystem
            file_path = document.file.path
            if os.path.exists(file_path):
                os.remove(file_path)

            # Delete the document from the database
            document.delete()

            return HttpResponseRedirect("document_list")
        except Exception as e:
            return HttpResponseRedirect("document_list")


class ToSignListView(LoginRequiredMixin, ListView):
    template_name = "documents/to_sign_list.html"
    context_object_name = "to_sign_documents"

    def get_queryset(self):
        """
        Get distinct documents that the user needs to sign, consolidating multiple required signatures.
        """
        return Document.objects.filter(
            signature_fields__assigned_user=self.request.user,
            signature_fields__signed=False
        ).annotate(num_signatures=Count('signature_fields'))


class AssignSignaturesView(LoginRequiredMixin, TemplateView):
    template_name = "documents/assign_signatures.html"

    def dispatch(self, request, *args, **kwargs):
        self.document = get_object_or_404(Document, pk=kwargs["pk"], owner=request.user)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["document"] = self.document
        # Exclude the owner if you want them not to sign, or show all users
        context["users"] = Account.objects.all().order_by("username")
        return context


class SaveSignaturesView(LoginRequiredMixin, View):
    def post(self, request, pk):
        document = get_object_or_404(Document, pk=pk)
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data"}, status=400)

        fields = data.get("signatures", [])
        if not fields:
            return JsonResponse({"error": "No signature fields provided"}, status=400)

        saved_fields = []
        pdf_path = document.file.path
        temp_pdf_path = os.path.join(settings.MEDIA_ROOT, f"temp_{document.file.name}")

        temp_dir = os.path.dirname(temp_pdf_path)  # Extract directory part of the path
        os.makedirs(temp_dir, exist_ok=True)  # Create it, including parents

        with open(pdf_path, "rb") as pdf_in:
            writer = IncrementalPdfFileWriter(pdf_in)

            for field in fields:
                user_id = field.get("assigned_user_id")
                x, y, width, height, page = field.get("x"), field.get("y"), field.get("width"), field.get(
                    "height"), field.get("page")

                if user_id is None or x is None or y is None or page is None or width is None or height is None:
                    continue

                assigned_user = get_object_or_404(Account, pk=user_id)
                field_name = f"Signature_{document.id}_{assigned_user.id}_{x}_{y}_{page}"

                signature_field, created = SignatureField.objects.update_or_create(
                    document=document,
                    assigned_user=assigned_user,
                    x=x,
                    y=y,
                    page=page,
                    width=width,
                    height=height,
                    defaults={"signed": False, "field_name": field_name},
                )

                spec = SigFieldSpec(
                    sig_field_name=field_name,
                    on_page=page - 1,  # Important: 0-based page index
                    box=(x, y, x + width, y + height)
                )

                append_signature_field(writer, spec)  # Use the imported function

                saved_fields.append({
                    "id": signature_field.id,
                    "user": assigned_user.username,
                    "x": signature_field.x,
                    "y": signature_field.y,
                    "width": signature_field.width,
                    "height": signature_field.height,
                    "page": signature_field.page,
                    "field_name": field_name,
                    "created": created,
                })

            with open(temp_pdf_path, "wb") as pdf_out:
                writer.write(pdf_out)

            os.replace(temp_pdf_path, pdf_path)

        return JsonResponse({"status": "Signatures saved successfully", "fields": saved_fields}, status=201)


class SignDocumentView(LoginRequiredMixin, View):
    def get(self, request, pk):
        """
        Display the PDF preview and any signature fields this user needs to sign.
        """
        document = get_object_or_404(Document, pk=pk)
        signature_fields = SignatureField.objects.filter(
            document=document,
            assigned_user=request.user,
            signed=False
        )

        # Convert QuerySet -> JSON for the template
        signature_fields_data = list(signature_fields.values("id", "x", "y", "page"))
        return render(
            request,
            "documents/sign_document.html",
            {
                "document": document,
                "signature_fields_json": json.dumps(signature_fields_data),
            },
        )

    def post(self, request, pk):
        document = get_object_or_404(Document, pk=pk)
        signature_fields = SignatureField.objects.filter(
            document=document, assigned_user=request.user, signed=False
        )

        if not signature_fields.exists():
            return JsonResponse({"error": "No pending signatures found"}, status=400)

        signature_path = get_user_signature_path(request.user)
        if not signature_path or not os.path.exists(signature_path):
            return JsonResponse({"error": "No registered signature image found"}, status=400)

        pdf_path = document.file.path
        temp_pdf_path = os.path.join(settings.MEDIA_ROOT, f"temp_{document.file.name}")
        signed_pdf_path = os.path.join(settings.MEDIA_ROOT, f"signed_documents/{document.file.name}")

        # Ensure directories exist
        os.makedirs(os.path.dirname(temp_pdf_path), exist_ok=True)
        os.makedirs(os.path.dirname(signed_pdf_path), exist_ok=True)

        with open(pdf_path, "rb") as pdf_in:
            writer = IncrementalPdfFileWriter(pdf_in)

            cert_path = os.path.join(settings.BASE_DIR, "certs/my_certificate.pfx")
            try:
                signer = signers.SimpleSigner.load_pkcs12(cert_path, passphrase=b"")  # Provide correct passphrase if needed
            except Exception as e:
                print(f"Error loading certificate: {e}")
                return JsonResponse({"error": "Error loading certificate"}, status=500)

            for field in signature_fields:
                try:
                    # 1. Load and scale image (PIL for size)
                    img = Image.open(signature_path)
                    img_width, img_height = img.size

                    max_width = field.width
                    max_height = field.height

                    scale_factor = min(max_width / img_width, max_height / img_height) if img_width and img_height else 1
                    scaled_width = int(img_width * scale_factor)
                    scaled_height = int(img_height * scale_factor)

                    # 2. Create PdfImage instance
                    pdf_image = PdfImage(signature_path, writer=writer)

                    # 3. Define the signature field spec
                    spec = SigFieldSpec(
                        sig_field_name=field.field_name,  # Or a unique name
                        on_page=field.page - 1,  # Page index is 0-based
                        box=(field.x, field.y, field.x + scaled_width, field.y + scaled_height)  # Use scaled dimensions
                    )

                    # 4. Sign the field (Crucially, handle appearance here!)
                    meta = PdfSignatureMetadata(field_name=field.field_name)
                    pdf_signer = PdfSigner(signature_meta=meta, signer=signer)

                    with open(temp_pdf_path, "wb") as temp_pdf:  # Sign to temp file first
                        pdf_signer.sign_pdf(writer, output=temp_pdf, existing_fields_only=True, appearance=pdf_image, sig_field_spec=spec)  # Pass spec and appearance

                    os.replace(temp_pdf_path, signed_pdf_path)  # Replace original with signed version

                except Exception as e:
                    print(f"Error signing field {field.field_name}: {e}")
                    return JsonResponse({"error": f"Error signing field {field.field_name}: {e}"}, status=500)

            signature_fields.update(signed=True)

        return JsonResponse({"status": "Signed successfully", "signed_pdf": signed_pdf_path})




