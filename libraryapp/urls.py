from django.urls import path
from .views import (
    FolderListCreateView, FolderDeleteView,
    NoteListCreateView, NoteDetailView,
    LibraryImageListCreateView
)
 
urlpatterns = [
    # Folders
    path('folders/', FolderListCreateView.as_view(), name='folder-list-create'),
    path('folders/<uuid:folder_id>/', FolderDeleteView.as_view(), name='folder-delete'),
 
    # Notes
    path('notes/', NoteListCreateView.as_view(), name='note-list-create'),
    path('notes/<uuid:note_id>/', NoteDetailView.as_view(), name='note-detail'),
]
