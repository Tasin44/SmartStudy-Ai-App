from django.db import models

# Create your models here
from django.db import models
from django.contrib.auth import get_user_model

import uuid

User = get_user_model()

# ── Storage Limits ─────────────────────────────────────────────────────────────
FREE_STORAGE_LIMIT_MB = 100        # 100 MB for free users
PAID_STORAGE_LIMIT_MB = None       # unlimited for paid users


# ── Folder ─────────────────────────────────────────────────────────────────────
 
class Folder(models.Model):
    """User-created folder to organize library items."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='folders', db_index=True)
    name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
 
    class Meta:
        ordering = ['name']
        indexes = [models.Index(fields=['user', 'name'])]
        # Prevent duplicate folder names per user
        unique_together = [('user', 'name')]
 
    def __str__(self):
        return f"Folder({self.user.email}, {self.name})"



# ── Note ───────────────────────────────────────────────────────────────────────
 
class Note(models.Model):
    """Text note with subject tag and optional folder."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notes', db_index=True)
 
    # Any subject string — not limited to predefined choices per requirement
    subject = models.CharField(max_length=100, db_index=True)
 
    title = models.CharField(max_length=300, blank=True, default='')
    text = models.TextField()
 
    # Optional folder — null means root-level item
    folder = models.ForeignKey(
        Folder, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='notes'
    )
 
    # AI-generated explanation of the note content
    ai_response = models.TextField(blank=True, default='')
 
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
 
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'subject']),
            models.Index(fields=['user', 'folder']),
        ]


# ── LibraryImage ───────────────────────────────────────────────────────────────
 
class LibraryImage(models.Model):
    """Image uploaded to library with subject tag."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='library_images', db_index=True)
 
    subject = models.CharField(max_length=100, db_index=True)
    title = models.CharField(max_length=300)
    image = models.ImageField(upload_to='library/images/')
    file_size_bytes = models.BigIntegerField(default=0)  # stored for storage limit checks
 
    folder = models.ForeignKey(
        Folder, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='images'
    )
    ai_response = models.TextField(blank=True, default='')
 
    created_at = models.DateTimeField(auto_now_add=True)
 
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'subject']),
            models.Index(fields=['user', 'folder']),
        ]


# ── LibraryFile ────────────────────────────────────────────────────────────────
 
ALLOWED_FILE_EXTENSIONS = ['pdf', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx', 'txt']
 
class LibraryFile(models.Model):
    """Document/file uploaded to library."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='library_files', db_index=True)
 
    subject = models.CharField(max_length=100, db_index=True)
    title = models.CharField(max_length=300)
    file = models.FileField(upload_to='library/files/')
    file_size_bytes = models.BigIntegerField(default=0)
    original_filename = models.CharField(max_length=300, blank=True, default='')
 
    folder = models.ForeignKey(
        Folder, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='files'
    )
    ai_response = models.TextField(blank=True, default='')
 
    created_at = models.DateTimeField(auto_now_add=True)
 
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'subject']),
            models.Index(fields=['user', 'folder']),
        ]


# ── UserStorageUsage ───────────────────────────────────────────────────────────
 
class UserStorageUsage(models.Model):
    """
    Tracks total bytes used per user.
    Updated on every upload/delete — single row per user,
    much cheaper than summing file_size_bytes on every request.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='storage_usage')
    total_bytes_used = models.BigIntegerField(default=0)
 
    def __str__(self):
        return f"Storage({self.user.email}: {self.total_bytes_used} bytes)"
 
    @property
    def used_mb(self):
        return round(self.total_bytes_used / (1024 * 1024), 2)#❓❓❓How the byte calculation is going on here












