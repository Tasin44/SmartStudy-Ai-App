from django.shortcuts import render
import os 
import httpx
# Create your views here.
from coreapp.mixins import StandardResponseMixin,extract_first_error
from coreapp.paginations import PageNumberPagination,StandardPagination
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .serializers import SendMessageSerializer,StartChatSerializer,ChatSessionSerializer
from .models import ChatSession,ChatMessage
#❓❓❓ why httpx used
def call_chat_ai(subject: str, history: list, user_message: str) -> str:#❓❓❓ what does they mean: subject:str,history:list,user_message:str
    """
    Sends full conversation history to OpenAI ChatCompletion.
    history = [{"role": "user"/"assistant", "content": "..."}, ...]
    """
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError(
            "AI service is not configured. "
            "Please ask the administrator to set OPENAI_API_KEY."
        )
 
    system_prompt = (
        f"You are an expert {subject} tutor. "
        f"Answer all questions clearly, step by step, with examples when needed. "
        f"Stay focused on {subject} topics."
    )

    #❓❓❓ what does two messages means? why they two used 
    # Build message list: system prompt + full history + new user message
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)                              # past conversation
    messages.append({"role": "user", "content": user_message})  # new message

    #❓❓❓am I passing here request and the ai response fetching 
    response = httpx.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": "gpt-4o", "messages": messages, "max_tokens": 1500},
        timeout=60.0
    )
 
    if response.status_code != 200:
        raise ValueError(
            f"AI service returned an error (status {response.status_code}). "
            "Please try again later."
        )
 
    return response.json()['choices'][0]['message']['content']#❓❓❓ explain this line
 

#❓❓❓what if I wants to use every modelname.objects.create() get_or_create instead

#❓❓❓why not I'm using just startchatserializer why not chatsession serialiser also?


class StartChatView(StandardResponseMixin, APIView):
    """
    POST /chat/start/
    Creates a new chat session for a subject.
    """
    permission_classes = [IsAuthenticated]
 
    def post(self, request):
        serializer = StartChatSerializer(data=request.data)
        if not serializer.is_valid():
            reason = extract_first_error(serializer.errors)
            return self.error_response(f"Could not start chat: {reason}", status_code=400)
 
        session = ChatSession.objects.create(
            user=request.user,
            subject=serializer.validated_data['subject'],
            title=serializer.validated_data.get('title', '').strip() or 'New Chat'
        )
        return self.success_response(
            ChatSessionSerializer(session).data,#❓❓❓ why I'm not using serializer.data? is it because I'll be only able to use serailzier.data when we use the same serializer at the top of the method and expect response from that ?
            message="Chat session started. You can now send messages.",
            status_code=201
        )



class SendMessageView(StandardResponseMixin,APIView):

    permission_classes=[IsAuthenticated]

    def post(self,request,session_id):

        try:
            session=ChatSession.objects.get(id=session_id,user=request.user)#❓❓❓ why not filter?

        except ChatSession.DoesNotExist:#❓❓❓ may I use here session.doesnotexist or just except?
            return  self.error_response(
                ""
            )
        serializer=SendMessageSerializer(data=request.data)
        
        



















