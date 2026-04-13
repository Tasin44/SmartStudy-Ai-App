import os
import base64
import httpx
from django.db.models import F, Q
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
 
from coreapp.mixins import StandardResponseMixin, extract_first_error
from coreapp.paginations import StandardPagination
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

        #this is the ai call part on note
        '''
        # Get AI explanation (non-blocking attempt — don't fail if AI is down)
        try:
            ai_response = call_text_ai(note.subject, note.text, mode='note')###❓❓❓what is the meaning of mode here
            note.ai_response = ai_response
            note.save(update_fields=['ai_response'])
        except Exception:
            pass  # AI failure shouldn't block note creation###❓❓❓what if I want to pass and error message here
        '''

 
        return self.success_response(
            NoteReadSerializer(note).data,
            message="Note saved successfully.",
            status_code=201
        )

class NoteDetailView(StandardResponseMixin, APIView):
    """GET / PATCH / DELETE /library/notes/<id>/"""
    permission_classes = [IsAuthenticated]
 
    def _get_note(self, request, note_id):
        try:
            return Note.objects.get(id=note_id, user=request.user)
        except Note.DoesNotExist:
            return None
 
    def get(self, request, note_id):
        note = self._get_note(request, note_id)
        if not note:
            return self.error_response("Note not found or access denied.", status_code=404)
        return self.success_response(NoteReadSerializer(note).data)
 
    def patch(self, request, note_id):
        note = self._get_note(request, note_id)
        if not note:
            return self.error_response("Note not found or access denied.", status_code=404)
 
        serializer = NoteCreateSerializer(note, data=request.data, partial=True)##❓❓❓ how could I know I've to pass them like note,data,partial on the serializer calling?
        if not serializer.is_valid():
            reason = extract_first_error(serializer.errors)
            return self.error_response(f"Note update failed: {reason}", status_code=400)
 
        note = serializer.save()##❓❓❓ how to know when I've to pass data inside serializer.save()?
        return self.success_response(NoteReadSerializer(note).data, message="Note updated.")
 
    def delete(self, request, note_id):
        note = self._get_note(request, note_id)
        if not note:
            return self.error_response("Note not found or access denied.", status_code=404)
        note.delete()
        return self.success_response({}, message="Note deleted successfully.")


# ── Library Image Views ────────────────────────────────────────────────────────
 
class LibraryImageListCreateView(StandardResponseMixin, APIView):
    """
    GET  /library/images/?subject=physics
    POST /library/images/   — checks storage quota before saving
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
 ##❓❓❓ why not I'm creating here a method like def _get_image(self, request, image_id):?
    def get(self, request): ###❓❓❓ why not image id considering here? like get(self,request,image_id)
        qs = LibraryImage.objects.filter(user=request.user)
        if subject := request.query_params.get('subject'):
            qs = qs.filter(subject=subject)
        if folder_id := request.query_params.get('folder_id'):
            qs = qs.filter(folder_id=folder_id)
 
        paginator = StandardPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(
            LibraryImageReadSerializer(page, many=True, context={'request': request}).data
        )
 ##❓❓❓ post method er starting e serializer call korte hoy, get method er response e serializer call korte hoy?
    def post(self, request):
        serializer = LibraryImageCreateSerializer(data=request.data)
        if not serializer.is_valid():
            reason = extract_first_error(serializer.errors)
            return self.error_response(f"Image upload failed: {reason}", status_code=400)
 
        image = serializer.validated_data['image']##❓❓❓ in serailizer, I've a method named validate_image, but here I'm calling validated_data[] for the image, why?
 
        # Enforce storage quota for free users
        allowed, reason = check_storage_quota(request.user, image.size)##❓❓❓ how this line working
        if not allowed:
            return self.error_response(reason, status_code=403)
 
        folder = serializer.validated_data.get('folder')##❓❓❓ for image I'm using "image=serializer.validated_data['image'] but for folder I'm using something different why? can't I use same ?
        if folder and folder.user != request.user:
            return self.error_response("Folder not found or access denied.", status_code=404)
 
        lib_image = serializer.save(##❓❓❓ how to know which thing I've to pass on serializer.save
            user=request.user,
            file_size_bytes=image.size
        )
 
        # Update storage tracker
        add_storage_usage(request.user, image.size)
 
        # AI vision analysis (best-effort)
        '''
        try:
            from scanapp.views import call_vision_ai
            ai_resp = call_vision_ai(image, lib_image.subject, '')
            lib_image.ai_response = ai_resp
            lib_image.save(update_fields=['ai_response'])
        except Exception:
            pass
        '''
 
        return self.success_response(
            LibraryImageReadSerializer(lib_image, context={'request': request}).data,
            message="Image uploaded and saved to library successfully.",
            status_code=201
        )


class LibraryImageDetailView(StandardResponseMixin,APIView):
    permission_classes=[IsAuthenticated]

    def _get_image(self,request,image_id):
        try:
            return LibraryImage.objects.get(id=image_id,user=request.user)
        except LibraryImage.DoesNotExist:
            return None
    
    def get(self,request,image_id):
        image=self._get_image(request,image_id)#❓❓❓ why passing here request? why not request.user?
        if not image:
            return self.error_response("Image not found",status_code=404)
        # return self.success_response(LibraryImageReadSerializer(image).data)
        return self.success_response(
            LibraryImageReadSerializer(image, context={'request': request}).data
        )

class LibraryImageDeleteView(StandardResponseMixin, APIView):
    """DELETE /library/images/<id>/"""
    permission_classes = [IsAuthenticated]
 
    def delete(self, request, image_id):
        try:
            img = LibraryImage.objects.get(id=image_id, user=request.user)
        except LibraryImage.DoesNotExist:
            return self.error_response("Image not found or access denied.", status_code=404)
 
        reduce_storage_usage(request.user, img.file_size_bytes)
        ##❓❓❓ what if I just do img.delete() , isn't it enough?
        img.image.delete(save=False)  # delete actual file from disk
        img.delete()
        return self.success_response({}, message="Image deleted successfully.")

# ── Library File Views ─────────────────────────────────────────────────────────
 
class LibraryFileListCreateView(StandardResponseMixin, APIView):
    """
    GET  /library/files/?subject=chemistry
    POST /library/files/   — checks storage quota
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
 
    def get(self, request):
        qs = LibraryFile.objects.filter(user=request.user)
        if subject := request.query_params.get('subject'):
            qs = qs.filter(subject=subject)
        if folder_id := request.query_params.get('folder_id'):
            qs = qs.filter(folder_id=folder_id)
 
        paginator = StandardPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(
            LibraryFileReadSerializer(page, many=True, context={'request': request}).data
        )
 
    def post(self, request):
        serializer = LibraryFileCreateSerializer(data=request.data)
        if not serializer.is_valid():
            reason = extract_first_error(serializer.errors)
            return self.error_response(f"File upload failed: {reason}", status_code=400)
 
        file = serializer.validated_data['file']
 
        allowed, reason = check_storage_quota(request.user, file.size)
        if not allowed:
            return self.error_response(reason, status_code=403)
 
        folder = serializer.validated_data.get('folder')
        if folder and folder.user != request.user:
            return self.error_response("Folder not found or access denied.", status_code=404)
 
        lib_file = serializer.save(
            user=request.user,
            file_size_bytes=file.size,
            original_filename=file.name
        )
 
        add_storage_usage(request.user, file.size)
 
        return self.success_response(
            LibraryFileReadSerializer(lib_file, context={'request': request}).data,
            message="File uploaded and saved to library successfully.",
            status_code=201
        )


class LibraryFileDeleteView(StandardResponseMixin, APIView):
    """DELETE /library/files/<id>/"""
    permission_classes = [IsAuthenticated]
 
    def delete(self, request, file_id):
        try:
            lib_file = LibraryFile.objects.get(id=file_id, user=request.user)
        except LibraryFile.DoesNotExist:
            return self.error_response("File not found or access denied.", status_code=404)
 
        reduce_storage_usage(request.user, lib_file.file_size_bytes)
        lib_file.file.delete(save=False)
        lib_file.delete()
        return self.success_response({}, message="File deleted successfully.")

class LibraryFileDetailView(StandardResponseMixin,APIView):
    permission_classes=[IsAuthenticated]

    def _get_file(self,request,file_id):
        try:
            return LibraryFile.objects.get(id=file_id,user=request.user)
        except LibraryFile.DoesNotExist:
            return None
    
    def get(self,request,file_id):
        file=self._get_file(request,file_id)
        if not file:
            return self.error_response("File not found",status_code=404)
        return self.success_response(
            LibraryFileReadSerializer(file,context={'request':request}).data
        )



##❓❓❓ Explain the whole method line by line
# ── Library Search ─────────────────────────────────────────────────────────────
 
class LibrarySearchView(StandardResponseMixin, APIView):
    """
    GET /library/search/?q=photosynthesis&type=notes&subject=biology
    Searches across notes, images, files, or all.
    """
    permission_classes = [IsAuthenticated]
 
    def get(self, request):
        query = request.query_params.get('q', '').strip()
        search_type = request.query_params.get('type', 'all')   # notes|images|files|folders|all
        subject = request.query_params.get('subject', '')
 
        if not query:
            return self.error_response(
                "Search query 'q' is required. Example: ?q=photosynthesis",
                status_code=400
            )
 
        result = {}
 
        # Search notes
        if search_type in ('notes', 'all'):
            note_qs = Note.objects.filter(
                user=request.user
            ).filter(
                Q(title__icontains=query) | Q(text__icontains=query) | Q(subject__icontains=query)
            )
            if subject:
                note_qs = note_qs.filter(subject__icontains=subject)
            result['notes'] = NoteReadSerializer(note_qs[:20], many=True).data
 
        # Search images
        if search_type in ('images', 'all'):
            img_qs = LibraryImage.objects.filter(
                user=request.user
            ).filter(
                Q(title__icontains=query) | Q(subject__icontains=query)
            )
            if subject:
                img_qs = img_qs.filter(subject__icontains=subject)
            result['images'] = LibraryImageReadSerializer(
                img_qs[:20], many=True, context={'request': request}
            ).data
 
        # Search files
        if search_type in ('files', 'all'):
            file_qs = LibraryFile.objects.filter(
                user=request.user
            ).filter(
                Q(title__icontains=query) | Q(subject__icontains=query) | Q(original_filename__icontains=query)
            )
            if subject:
                file_qs = file_qs.filter(subject__icontains=subject)
            result['files'] = LibraryFileReadSerializer(
                file_qs[:20], many=True, context={'request': request}
            ).data
 
        # Search folders
        if search_type in ('folders', 'all'):
            folder_qs = Folder.objects.filter(
                user=request.user,
                name__icontains=query
            )
            result['folders'] = FolderSerializer(folder_qs[:20], many=True).data
 
        return self.success_response(result, message="Search results fetched.")




class LibraryOverviewView(StandardResponseMixin, APIView):
    """
    GET /library/overview/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        notes_qs = Note.objects.filter(user=request.user)
        images_qs = LibraryImage.objects.filter(user=request.user)
        folders_qs = Folder.objects.filter(user=request.user)

        notes_data = NoteReadSerializer(notes_qs, many=True).data
        images_data = LibraryImageReadSerializer(
            images_qs, many=True, context={"request": request}
        ).data
        folders_data = FolderSerializer(folders_qs, many=True).data

        notes_count = notes_qs.count()
        images_count = images_qs.count()
        folders_count = folders_qs.count()
        total_count = notes_count + images_count + folders_count

        return self.success_response(
            {
                "notes": {"count": notes_count, "items": notes_data},
                "images": {"count": images_count, "items": images_data},
                "folders": {"count": folders_count, "items": folders_data},
                "total_count": total_count
            },
            message="Library overview fetched successfully."
        )
    

class FolderContentsView(StandardResponseMixin, APIView):
    """
    GET /library/folders/<folder_id>/contents/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, folder_id):
        try:
            folder = Folder.objects.get(id=folder_id, user=request.user)
        except Folder.DoesNotExist:
            return self.error_response("Folder not found or access denied.", status_code=404)

        notes_qs = Note.objects.filter(user=request.user, folder=folder)
        images_qs = LibraryImage.objects.filter(user=request.user, folder=folder)
        files_qs = LibraryFile.objects.filter(user=request.user, folder=folder)

        return self.success_response(
            {
                "folder": FolderSerializer(folder).data,
                "notes": {
                    "count": notes_qs.count(),
                    "items": NoteReadSerializer(notes_qs, many=True).data
                },
                "images": {
                    "count": images_qs.count(),
                    "items": LibraryImageReadSerializer(
                        images_qs, many=True, context={"request": request}
                    ).data
                },
                "files": {
                    "count": files_qs.count(),
                    "items": LibraryFileReadSerializer(
                        files_qs, many=True, context={"request": request}
                    ).data
                },
                "total_count": notes_qs.count() + images_qs.count() + files_qs.count()
            },
            message="Folder contents fetched successfully."
        )




























