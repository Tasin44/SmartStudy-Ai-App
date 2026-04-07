from django.shortcuts import render
import os 
import httpx
# Create your views here.
from coreapp.mixins import StandardResponseMixin,extract_first_error
from coreapp.paginations import PageNumberPagination,StandardPagination
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .serializers import SendMessageSerializer,StartChatSerializer,ChatSessionSerializer,ChatMessageSerializer
from .models import ChatSession,ChatMessage
from profileapp.models import UserProfile
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



class SendMessageView(StandardResponseMixin, APIView):
    """
    POST /chat/<session_id>/message/
    Send a message, get AI reply. Full history is sent to AI each time.
    """
    permission_classes = [IsAuthenticated]
 
    def post(self, request, session_id):
        # Verify session ownership — users cannot access other users' chats
        try:
            session = ChatSession.objects.get(id=session_id, user=request.user)#❓❓❓ why not filter,why .get?
            #❓❓❓ why chatsession checking is necessary in this view?
        except ChatSession.DoesNotExist:#❓❓❓ may I use here session.doesnotexist or just except?
            return self.error_response(
                "Chat session not found or you do not have permission to access it.",
                status_code=404
            )
 
        serializer = SendMessageSerializer(data=request.data)
        if not serializer.is_valid():
            reason = extract_first_error(serializer.errors)
            return self.error_response(f"Message invalid: {reason}", status_code=400)
 
        user_text = serializer.validated_data['message']
 
        # Fetch last 20 messages for context (prevents huge payloads to AI)
        # Only fetch role + content — we don't need id/created_at for the AI call
        past_messages = list(# #❓❓❓why this list() used? 
            session.messages# ChatMessage model 'session' field related name
            .values('role', 'content')
            .order_by('created_at')[:20]         # oldest first, limit 20
        )
 
        # Call AI with history
        try:
            ai_reply = call_chat_ai(session.subject, past_messages, user_text)
        except ValueError as e:
            return self.error_response(str(e), status_code=503)
        except Exception:
            return self.error_response(
                "AI service is temporarily unavailable. Please try again shortly.",
                status_code=503
            )
 
        # Save both messages in bulk to minimize DB round trips
        #❓❓❓ why this bulk creation doing here
        #❓❓❓this 3(session,role,content) is the mandatory field
        ChatMessage.objects.bulk_create([
            ChatMessage(session=session, role=ChatMessage.ROLE_USER, content=user_text),
            ChatMessage(session=session, role=ChatMessage.ROLE_AI, content=ai_reply),
        ])
 
        # Update session timestamp so ordering works correctly
        session.save(update_fields=['updated_at'])
 
        # Increment problems_solved counter
        from django.db.models import F
        UserProfile.objects.filter(user=request.user).update(
            problems_solved=F('problems_solved') + 1
        )
 
        return self.success_response(
            {"role": "assistant", "content": ai_reply},
            message="Message sent and AI response received.",
            status_code=200
        )
        


        




class ChatHistoryView(StandardResponseMixin,APIView):

    permission_classes=[IsAuthenticated]

    def get(self,requst,session_id):
        try:
            session = ChatSession.objects.get(id=session_id,user=self.request.user)
        except ChatSession.DoesNotExist:
            return self.error_response(
                "Chat session not found",
                status_code=404
            )
        
        
        messages=session.messages.all()#chatmessage model connected with chatsession model with the related name messages that why this  messages used right?
        paginator=StandardPagination()


class ChatHistoryView(StandardResponseMixin, APIView):
    """
    GET /chat/<session_id>/messages/
    Returns paginated message history for a session.
    """
    permission_classes = [IsAuthenticated]
 
    def get(self, request, session_id):
        try:
            session = ChatSession.objects.get(id=session_id, user=request.user)
        except ChatSession.DoesNotExist:
            return self.error_response(
                "Chat session not found or access denied.",
                status_code=404
            )
        
        #❓❓❓ what if I want to write the serializer line here serializer = ChatMessageSerializer(page, many=True)
        #❓❓❓how to know I should use this below 4 field here, messages,paginator,page,
        messages = session.messages.all()#chatmessage model connected with chatsession model with the related name messages that why this  messages used right?
        paginator = StandardPagination()
        page = paginator.paginate_queryset(messages, request)
        serializer = ChatMessageSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
 


class ChatSessionListView(StandardResponseMixin, APIView):
    """
    GET /chat/sessions/?subject=math
    Lists all chat sessions for the logged-in user.
    """
    permission_classes = [IsAuthenticated]
 
    def get(self, request):
        qs = ChatSession.objects.filter(user=request.user)#❓❓❓ what is qs here?
        subject = request.query_params.get('subject')
        if subject:
            qs = qs.filter(subject=subject)
 
        paginator = StandardPagination()
        page = paginator.paginate_queryset(qs, request)
        serializer = ChatSessionSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)























