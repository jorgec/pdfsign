from django.urls import path
from .views import UploadDocumentView, DocumentListView, ToSignListView, SignDocumentView, AssignSignaturesView, \
    SaveSignaturesView, DeleteDocumentView

urlpatterns = [
    path("upload/", UploadDocumentView.as_view(), name="upload_document"),
    path("uploads/", DocumentListView.as_view(), name="document_list"),
    path("to_sign/", ToSignListView.as_view(), name="to_sign_list"),
    path("sign/<int:pk>/", SignDocumentView.as_view(), name="sign_document"),
    path("assign_signatures/<int:pk>/", AssignSignaturesView.as_view(), name="assign_signatures"),
    path("save_signatures/<int:pk>/", SaveSignaturesView.as_view(), name="save_signatures"),
    path("delete/<int:pk>/", DeleteDocumentView.as_view(), name="delete_document"),

]
