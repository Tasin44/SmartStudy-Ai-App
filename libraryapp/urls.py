from django.urls import path
from .views import (
    FolderListCreateView, FolderDeleteView,
    NoteListCreateView, NoteDetailView,
    LibraryImageListCreateView, LibraryImageDeleteView,
    LibraryFileListCreateView, LibraryFileDeleteView,
    LibrarySearchView,
)
 
urlpatterns = [
    # Folders
    path('folders/', FolderListCreateView.as_view(), name='folder-list-create'),
    path('folders/<uuid:folder_id>/', FolderDeleteView.as_view(), name='folder-delete'),
 
    # Notes
    path('notes/', NoteListCreateView.as_view(), name='note-list-create'),
    path('notes/<uuid:note_id>/', NoteDetailView.as_view(), name='note-detail'),

    # Images
    path('images/', LibraryImageListCreateView.as_view(), name='library-image-list-create'),
    path('images/<uuid:image_id>/', LibraryImageDeleteView.as_view(), name='library-image-delete'),
 
    # Files
    path('files/', LibraryFileListCreateView.as_view(), name='library-file-list-create'),
    path('files/<uuid:file_id>/', LibraryFileDeleteView.as_view(), name='library-file-delete'),
 
    # Search
    path('search/', LibrarySearchView.as_view(), name='library-search'),


]
