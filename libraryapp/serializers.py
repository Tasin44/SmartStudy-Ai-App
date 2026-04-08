
from rest_framework import serializers
from .models import (
    Note, LibraryImage, LibraryFile, Folder,
    ALLOWED_FILE_EXTENSIONS, FREE_STORAGE_LIMIT_MB
)
 

# ── Folder ─────────────────────────────────────────────────────────────────────
 
class FolderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Folder
        fields = ['id', 'name', 'created_at', 'updated_at']#❓❓❓ folder model also containing user field, why not it's considering here
        read_only_fields = ['id', 'created_at', 'updated_at']
 
    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Folder name cannot be blank.")
        return value


# ── Note ───────────────────────────────────────────────────────────────────────
 
class NoteCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = ['subject', 'title', 'text', 'folder']
        extra_kwargs = {#❓❓❓why  folder allow null true, why not allow blank true, why title allow blank true, why not null treu
            'folder': {'required': False, 'allow_null': True},
            'title': {'required': False, 'allow_blank': True},
        }
 
    def validate_subject(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Subject name cannot be blank.")
        return value
 
    def validate_text(self, value):
        if not value.strip():
            raise serializers.ValidationError("Note text cannot be empty.")
        return value

class NoteReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = ['id', 'subject', 'title', 'text', 'ai_response', 'folder', 'created_at', 'updated_at']


# ── LibraryImage ───────────────────────────────────────────────────────────────
 
class LibraryImageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LibraryImage
        fields = ['subject', 'title', 'image', 'folder']
        extra_kwargs = {
            'folder': {'required': False, 'allow_null': True},
        }
 
    def validate_subject(self, value):#❓❓❓ why _ for _ in() used here 
        return value.strip() or (_ for _ in ()).throw(
            serializers.ValidationError("Subject cannot be blank.")
        )
 
    def validate_title(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Title cannot be blank.")
        return value
 
    def validate_image(self, value):
        # 10 MB per image limit
        if value.size > 10 * 1024 * 1024:#❓❓❓explain this calc
            raise serializers.ValidationError(
                "Image is too large. Maximum allowed size is 10 MB."
            )
        return value

class LibraryImageReadSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
 
    class Meta:
        model = LibraryImage
        fields = ['id', 'subject', 'title', 'image_url', 'file_size_bytes', 'ai_response', 'folder', 'created_at']
 
    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None

# ── LibraryFile ────────────────────────────────────────────────────────────────
 
class LibraryFileCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LibraryFile
        fields = ['subject', 'title', 'file', 'folder']
        extra_kwargs = {
            'folder': {'required': False, 'allow_null': True},
        }
 
    def validate_title(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Title cannot be blank.")
        return value
 
    def validate_file(self, value):
        # Check file extension against allowed list
        ext = value.name.rsplit('.', 1)[-1].lower()#❓❓❓ explain this line
        if ext not in ALLOWED_FILE_EXTENSIONS:
            raise serializers.ValidationError(
                f"File type '{ext}' is not allowed. "
                f"Accepted types: {', '.join(ALLOWED_FILE_EXTENSIONS)}."
            )
        # 50 MB per file limit
        if value.size > 50 * 1024 * 1024:
            raise serializers.ValidationError(
                "File is too large. Maximum allowed size is 50 MB."
            )
        return value
 
 
class LibraryFileReadSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
 
    class Meta:
        model = LibraryFile
        fields = ['id', 'subject', 'title', 'file_url', 'original_filename',
                  'file_size_bytes', 'ai_response', 'folder', 'created_at']
 
    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None











