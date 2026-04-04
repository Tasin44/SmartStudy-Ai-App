


from rest_framework import serializers
from scanapp.models import SUBJECT_CHOICES
from .models import ChatMessage,ChatSession

##❓❓❓ what is the work of all of this individual serializer
class StartChatSerializer(serializers.Serializer):
    """Create a new chat session."""
    subject = serializers.ChoiceField(choices=[c[0] for c in SUBJECT_CHOICES])
    title = serializers.CharField(max_length=200, required=False, allow_blank=True)
 
 
class SendMessageSerializer(serializers.Serializer):
    """Send a message in an existing session."""
    message = serializers.CharField(min_length=1, max_length=2000)

#❓❓❓what is the differnce between serializers.serializers and serializers.modelserializers?

class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ['id', 'role', 'content', 'created_at']
 
 
class ChatSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatSession
        fields = ['id', 'subject', 'title', 'created_at', 'updated_at']
 

















