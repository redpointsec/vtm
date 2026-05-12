from chatbot.models import ChatSession


def chat_sessions(request):
    """Provide active chat sessions for the user in all templates."""
    sessions = []
    if request.user.is_authenticated:
        sessions = ChatSession.objects.filter(
            user=request.user, is_active=True
        ).order_by('-created_at')[:20]
    return {'chat_sessions': sessions}
