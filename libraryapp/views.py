import os
import base64
import httpx
from django.db.models import F, Q
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
 
from coreapp.mixins import StandardResponseMixin, extract_first_error
from coreapp.pagination import StandardPagination
from .models import (
    Note, LibraryImage, LibraryFile, Folder,
    UserStorageUsage, FREE_STORAGE_LIMIT_MB
)
from .serializers import (
    FolderSerializer,
    NoteCreateSerializer, NoteReadSerializer,
    LibraryImageCreateSerializer, LibraryImageReadSerializer,
    LibraryFileCreateSerializer, LibraryFileReadSerializer,
)

# ── Storage Enforcement Helper ────────────────────────────────────────────────
 
def check_storage_quota(user, new_file_bytes: int) -> tuple[bool, str]:#❓❓❓why -> used?
    """
    Returns (is_allowed: bool, reason: str).
    Free users get FREE_STORAGE_LIMIT_MB. Paid users are unlimited.
    Uses get_or_create so storage row always exists.
    """
    # Check if user is paid (you can adjust this to your subscription model)
    is_paid = getattr(user, 'is_paid', False)
    if is_paid:
        return True, ""
 
    usage, _ = UserStorageUsage.objects.get_or_create(user=user)#❓❓❓why _ used here?
    limit_bytes = FREE_STORAGE_LIMIT_MB * 1024 * 1024
 
    if usage.total_bytes_used + new_file_bytes > limit_bytes:
        remaining_mb = round((limit_bytes - usage.total_bytes_used) / (1024 * 1024), 2)
        return False, (
            f"Storage limit reached. Free users get {FREE_STORAGE_LIMIT_MB} MB. "
            f"You have {remaining_mb} MB remaining. "
            f"Upgrade to a paid plan for unlimited storage."
        )
    return True, ""


def add_storage_usage(user, bytes_added: int):
    """Atomically add bytes to user's storage tracker."""
    UserStorageUsage.objects.update_or_create(#❓❓❓why update or create why not get or create?
        user=user,
        defaults={},
    )
    UserStorageUsage.objects.filter(user=user).update(
        total_bytes_used=F('total_bytes_used') + bytes_added
    )
 
 
def reduce_storage_usage(user, bytes_removed: int):
    """Atomically reduce bytes after a file is deleted."""
    UserStorageUsage.objects.filter(user=user).update(
        total_bytes_used=F('total_bytes_used') - bytes_removed#❓❓❓why F used here, how the calculation is going on here
    )



# ── AI Helper (text-based) ────────────────────────────────────────────────────
 
def call_text_ai(subject: str, content: str, mode: str = 'note') -> str:
    """
    Asks AI to explain/summarize text content (note or file text).
    mode: 'note' | 'file'
    """
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("AI service not configured. Set OPENAI_API_KEY in .env.")
 
    system_prompt = (
        f"You are an expert {subject} tutor. "
        f"{'Explain this note' if mode == 'note' else 'Summarize and explain this document'} "
        f"clearly and concisely."
    )
 
    response = httpx.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": "gpt-4o",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content[:4000]}  # cap at 4000 chars
            ],
            "max_tokens": 1000
        },
        timeout=60.0#❓❓❓what is timeout here
    )
 
    if response.status_code != 200:
        raise ValueError(f"AI service error (status {response.status_code}).")
 
    return response.json()['choices'][0]['message']['content']#❓❓❓explain this line



# ── Folder Views ───────────────────────────────────────────────────────────────
 
class FolderListCreateView(StandardResponseMixin, APIView):
    """
    GET  /library/folders/       — list user's folders
    POST /library/folders/       — create a new folder
    """
    permission_classes = [IsAuthenticated]
 
    def get(self, request):
        folders = Folder.objects.filter(user=request.user)#❓❓❓explain this line 
        paginator = StandardPagination()#❓❓❓why 
        page = paginator.paginate_queryset(folders, request)
        return paginator.get_paginated_response(FolderSerializer(page, many=True).data)
 
    def post(self, request):
        serializer = FolderSerializer(data=request.data)
        if not serializer.is_valid():
            reason = extract_first_error(serializer.errors)
            return self.error_response(f"Folder creation failed: {reason}", status_code=400)
 
        # Check for duplicate name — serializer layer + DB unique_together
        name = serializer.validated_data['name']
        if Folder.objects.filter(user=request.user, name=name).exists():
            return self.error_response(
                f"A folder named '{name}' already exists. Please choose a different name.",
                status_code=409#❓❓❓why 409
            )
 
        folder = serializer.save(user=request.user)#❓❓❓why
        return self.success_response(
            FolderSerializer(folder).data,
            message=f"Folder '{folder.name}' created successfully.",
            status_code=201
        )


class FolderDeleteView(StandardResponseMixin,APIView):

    permission_classes =[IsAuthenticated]

    def delete(self,request,folder_id):
        try:
            folder= Folder.objects.get(id=folder_id,user = request.user)
        except Folder.DoesNotExist:
            return self.error_response(f"Folder not found",status_code=404)


class FolderDeleteView(StandardResponseMixin, APIView):
    """DELETE /library/folders/<id>/"""
    permission_classes = [IsAuthenticated]
 
    def delete(self, request, folder_id):
        try:
            folder = Folder.objects.get(id=folder_id, user=request.user)#❓❓❓why id and user both passing on the get() method, and also how to know which thing I've to pass during this type of get
        except Folder.DoesNotExist:
            return self.error_response("Folder not found or access denied.", status_code=404)
 
        folder.delete() ##❓❓❓ is delete built in here? what is folder here?  how many builtin its containing explain 
        return self.success_response({}, message="Folder deleted successfully.")




#❓❓❓Do we 've to always pass user=request.user on the .get() and .filter()?

# ── Note Views ─────────────────────────────────────────────────────────────────
 
class NoteListCreateView(StandardResponseMixin, APIView):
    """
    GET  /library/notes/?subject=math&folder_id=<uuid>
    POST /library/notes/
    """
    permission_classes = [IsAuthenticated]
 
    def get(self, request):#❓❓❓explain below all lines
        qs = Note.objects.filter(user=request.user)
        if subject := request.query_params.get('subject'):
            qs = qs.filter(subject=subject)
        if folder_id := request.query_params.get('folder_id'):
            qs = qs.filter(folder_id=folder_id)
 
        paginator = StandardPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(NoteReadSerializer(page, many=True).data)
 
    def post(self, request):
        serializer = NoteCreateSerializer(data=request.data)
        if not serializer.is_valid():
            reason = extract_first_error(serializer.errors)
            return self.error_response(f"Note creation failed: {reason}", status_code=400)
 
        # Validate folder belongs to this user if provided###❓❓❓why not  folder = serializer.validated_data['folder ']
        folder = serializer.validated_data.get('folder')###❓❓❓ there is no folder validaton logic on the notecreateserializer, then how it's calling here?
        if folder and folder.user != request.user:
            return self.error_response("Folder not found or access denied.", status_code=404)
 
        note = serializer.save(user=request.user)
 
         ###❓❓❓ can I call the subject and text like this and later use them on the ai_response
        #subject = serializer.validate_subject.get('subject')
        #text = serializer.validate_text.get('text')

        # Get AI explanation (non-blocking attempt — don't fail if AI is down)
        try:
            ai_response = call_text_ai(note.subject, note.text, mode='note')###❓❓❓what is the meaning of mode here
            note.ai_response = ai_response
            note.save(update_fields=['ai_response'])
        except Exception:
            pass  # AI failure shouldn't block note creation###❓❓❓what if I want to pass and error message here
 
        return self.success_response(
            NoteReadSerializer(note).data,
            message="Note saved successfully.",
            status_code=201
        )































