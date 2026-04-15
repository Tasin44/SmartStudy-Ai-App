from django.contrib import admin
from .models import Folder, Note, LibraryImage, LibraryFile, UserStorageUsage

@admin.register(Folder)
class FolderAdmin(admin.ModelAdmin):
	list_display = ('id', 'user', 'name', 'created_at', 'updated_at')
	search_fields = ('user__email', 'name')


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
	list_display = ('id', 'user', 'subject', 'title', 'created_at')
	search_fields = ('user__email', 'subject', 'title', 'text')
	list_filter = ('subject',)


@admin.register(LibraryImage)
class LibraryImageAdmin(admin.ModelAdmin):
	list_display = ('id', 'user', 'subject', 'title', 'file_size_bytes', 'created_at')
	search_fields = ('user__email', 'subject', 'title')
	list_filter = ('subject',)


@admin.register(LibraryFile)
class LibraryFileAdmin(admin.ModelAdmin):
	list_display = ('id', 'user', 'subject', 'title', 'original_filename', 'file_size_bytes', 'created_at')
	search_fields = ('user__email', 'subject', 'title', 'original_filename')
	list_filter = ('subject',)


@admin.register(UserStorageUsage)
class UserStorageUsageAdmin(admin.ModelAdmin):
	list_display = ('id', 'user', 'total_bytes_used')
	search_fields = ('user__email',)
