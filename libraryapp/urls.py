from django.urls import path
from .views import (
    FolderListCreateView, FolderDeleteView,
    NoteListCreateView, NoteDetailView,
    LibraryImageListCreateView, LibraryImageDeleteView,
    LibraryFileListCreateView, LibraryFileDeleteView,
    LibrarySearchView,LibraryOverviewView,FolderContentsView,LibraryImageDetailView,LibraryFileDetailView
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
    path('images/<uuid:image_id>/delete', LibraryImageDeleteView.as_view(), name='library-image-delete'),
    path('images/<uuid:image_id>/', LibraryImageDetailView.as_view(), name='library-image-detail'),
 
    # Files
    path('files/', LibraryFileListCreateView.as_view(), name='library-file-list-create'),
    path('files/<uuid:file_id>/delete/', LibraryFileDeleteView.as_view(), name='library-file-delete'),
    path('files/<uuid:file_id>/', LibraryFileDetailView.as_view(), name='library-file-delete'),
    # Search
    path('search/', LibrarySearchView.as_view(), name='library-search'),

    path('overview/',LibraryOverviewView.as_view(),name='library-overview'),

    path('folders/<uuid:folder_id>/contents/',FolderContentsView.as_view(),name='folder-contents'),

]
