



from rest_framework import serializers
from .models import (
    Note, LibraryImage, LibraryFile, Folder,
    ALLOWED_FILE_EXTENSIONS, FREE_STORAGE_LIMIT_MB
)
 

class FolderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Folder
        pass






























