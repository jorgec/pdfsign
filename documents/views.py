from django.core.exceptions import PermissionDenied
import json
import os

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
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.sign import signers
from pyhanko.sign.signers.pdf_signer import PdfSigner, PdfSignatureMetadata
from pyhanko.sign.fields import enumerate_sig_fields, SigFieldSpec, append_signature_field

from accounts.models import Account
from signatures.utils import get_user_signature_path
from .forms import DocumentUploadForm
from .models import Document, SignatureField
from .utils import remove_hybrid_xrefs

from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, DictionaryObject, ArrayObject, NumberObject  # ✅ Fix for DictionaryObject
from PIL import Image


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
    """
    Saves the signature locations for a document and assigns them to users.
    Also ensures that the PDF has the necessary AcroForm fields.
    """

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

        with open(pdf_path, "rb") as pdf_in:
            writer = IncrementalPdfFileWriter(pdf_in)

            # Ensure PDF has an AcroForm
            root = writer.root
            if "/AcroForm" not in root:
                acroform_dict = DictionaryObject({
                    NameObject("/Fields"): writer.add_object(ArrayObject([]))
                })
                root[NameObject("/AcroForm")] = writer.add_object(acroform_dict)

            acro_form = root["/AcroForm"]

            # Ensure AcroForm has a "/Fields" array
            if "/Fields" not in acro_form:
                acro_form[NameObject("/Fields")] = writer.add_object(ArrayObject([]))

            for field in fields:
                user_id = field.get("assigned_user_id")
                x, y, page = field.get("x"), field.get("y"), field.get("page")

                if user_id is None or x is None or y is None or page is None:
                    continue  # Skip invalid field entries

                assigned_user = get_object_or_404(Account, pk=user_id)

                # Generate a unique field name
                field_name = f"Signature_{document.id}_{assigned_user.id}_{x}_{y}_{page}"

                # Create or update signature field in the database
                signature_field, created = SignatureField.objects.update_or_create(
                    document=document,
                    assigned_user=assigned_user,
                    x=x,
                    y=y,
                    page=page,
                    defaults={"signed": False, "field_name": field_name},
                )

                # Add signature field to the PDF
                spec = SigFieldSpec(
                    sig_field_name=field_name,
                    on_page=page - 1,  # PyHanko uses 0-based indexing
                    box=(x, y, x + 100, y + 50)
                )
                append_signature_field(writer, spec)

                saved_fields.append({
                    "id": signature_field.id,
                    "user": assigned_user.username,
                    "x": signature_field.x,
                    "y": signature_field.y,
                    "page": signature_field.page,
                    "field_name": field_name,
                    "created": created,
                })

            # Save the updated PDF with AcroForm fields
            with open(temp_pdf_path, "wb") as pdf_out:
                writer.write(pdf_out)

            # Replace the original PDF
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

        # Ensure user has an uploaded signature image
        signature_path = get_user_signature_path(request.user)
        if not signature_path or not os.path.exists(signature_path):
            return JsonResponse({"error": "No registered signature image found"}, status=400)

        # Paths for input & output
        pdf_path = document.file.path
        temp_pdf_path = os.path.join(settings.MEDIA_ROOT, f"temp_{document.file.name}")
        signed_pdf_path = os.path.join(settings.MEDIA_ROOT, f"signed_documents/{document.file.name}")

        # Step 1: Ensure PDF has signature fields & overlay the signature image
        reader = PdfReader(pdf_path)
        writer = PdfWriter()

        for page_number in range(len(reader.pages)):
            page = reader.pages[page_number]

            # Get all signature fields on this page
            page_fields = [
                field for field in signature_fields if field.page == page_number + 1
            ]

            for field in page_fields:
                # Load the signature image
                img = Image.open(signature_path)
                img_width, img_height = img.size

                # Convert image to an annotation
                annotation = DictionaryObject({
                    NameObject("/Type"): NameObject("/Annot"),
                    NameObject("/Subtype"): NameObject("/Stamp"),
                    NameObject("/Rect"): ArrayObject([
                        NumberObject(field.x),
                        NumberObject(field.y),
                        NumberObject(field.x + img_width / 3),  # Scale down if needed
                        NumberObject(field.y + img_height / 3)
                    ]),
                    NameObject("/NM"): NameObject(field.field_name),
                    NameObject("/P"): page.indirect_reference
                })

                # Add annotation to page
                if "/Annots" in page:
                    page["/Annots"].append(annotation)
                else:
                    page[NameObject("/Annots")] = ArrayObject([annotation])

            # Add modified page to writer
            writer.add_page(page)

        # Ensure output directories exist before writing
        os.makedirs(os.path.dirname(temp_pdf_path), exist_ok=True)
        os.makedirs(os.path.dirname(signed_pdf_path), exist_ok=True)

        # Save the PDF with the signature overlay
        with open(temp_pdf_path, "wb") as temp_pdf:
            writer.write(temp_pdf)

        # Step 2: Ensure the signature fields exist before signing
        with open(temp_pdf_path, "rb") as pdf_in:
            writer = IncrementalPdfFileWriter(pdf_in)

            # Ensure the PDF has an AcroForm
            root = writer.root
            if "/AcroForm" not in root:
                acroform_dict = DictionaryObject({
                    NameObject("/Fields"): writer.add_object(ArrayObject())
                })
                root[NameObject("/AcroForm")] = writer.add_object(acroform_dict)

            acro_form = root["/AcroForm"]

            # Ensure the AcroForm has a "/Fields" array
            if "/Fields" not in acro_form:
                acro_form[NameObject("/Fields")] = writer.add_object(ArrayObject())

            # Retrieve assigned field names
            field_names = [field.field_name for field in signature_fields]
            if not field_names:
                return JsonResponse({"error": "No valid signature fields found"}, status=400)

            # **Debugging: Print available fields before signing**
            available_fields = list(enumerate_sig_fields(writer))
            available_field_names = [field.field_name for field in available_fields]
            print(f"Available Signature Fields: {available_field_names}")

            # Verify fields exist
            for field_name in field_names:
                if field_name not in available_field_names:
                    return JsonResponse({"error": f"Signature field '{field_name}' not found in the PDF"}, status=400)

            # Load certificate & private key
            cert_path = os.path.join(settings.BASE_DIR, "certs/my_certificate.pfx")
            signer = signers.SimpleSigner.load_pkcs12(
                cert_path,
                passphrase=b""
            )

            # Sign each field explicitly
            for field_name in field_names:
                meta = PdfSignatureMetadata(field_name=field_name)

                pdf_signer = PdfSigner(
                    signature_meta=meta,
                    signer=signer,
                )

                with open(signed_pdf_path, "wb") as pdf_out:
                    pdf_signer.sign_pdf(
                        writer,
                        output=pdf_out,
                        existing_fields_only=True,
                    )

            # Mark fields as signed in the database
            signature_fields.update(signed=True)

        return JsonResponse({"status": "Signed successfully", "signed_pdf": signed_pdf_path})
