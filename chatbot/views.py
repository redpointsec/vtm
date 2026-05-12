import json
import time

from openai import OpenAI
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import StreamingHttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from chatbot.models import ChatMessage, ChatSession
from chatbot.tools import get_overview, get_tools

SYSTEM_PROMPT = (
    "You are a helpful assistant for the VTAM (Vulnerable Task Asset Manager). "
    "You can help users manage their projects and tasks. "
    "Use the available tools to query live data when needed. "
    "The local context snapshot is authoritative for the current user, but may be incomplete. "
    "Be concise and helpful in your responses."
)

_openai_client = None


def _get_openai_client():
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=getattr(settings, 'OPENAI_BASE_URL', None),
        )
    return _openai_client


def _run_react_loop(user, user_message, conversation_history=None):
    """Run a ReAct loop using the OpenAI API with tool use."""
    client = _get_openai_client()
    tools = get_tools()

    messages = [
        {'role': 'system', 'content': SYSTEM_PROMPT},
        {
            'role': 'system',
            'content': f'Current VTAM data for {user.username}:\n{get_overview(user)}',
        },
    ]
    if conversation_history:
        messages.extend(conversation_history)
    messages.append({'role': 'user', 'content': user_message})

    # Wrap each tool with the "type": "function" field expected by the API
    api_tools = [{'type': 'function', 'function': t['function']} for t in tools.values()]

    final_text = ''
    iterations = 0
    max_iterations = 10

    while iterations < max_iterations:
        iterations += 1
        kwargs = {
            'model': settings.OPENAI_MODEL,
            'messages': messages,
            'tools': api_tools,
            'tool_choice': 'auto',
        }

        response = client.chat.completions.create(**kwargs)
        choice = response.choices[0]

        if choice.finish_reason == 'stop':
            final_text += (choice.message.content or '')
            break

        if choice.finish_reason == 'tool_calls':
            final_text += (choice.message.content or '')
            tool_calls = choice.message.tool_calls or []
            messages.append({
                'role': 'assistant',
                'content': choice.message.content,
                'tool_calls': [
                    {
                        'id': tc.id,
                        'type': tc.type,
                        'function': {
                            'name': tc.function.name,
                            'arguments': tc.function.arguments,
                        },
                    }
                    for tc in tool_calls
                ],
            })
            for tc in tool_calls:
                tool_name = tc.function.name
                try:
                    tool_args = json.loads(tc.function.arguments or '{}')
                except json.JSONDecodeError:
                    tool_args = {}
                tool_result = _execute_tool(tool_name, tool_args, user)

                messages.append({
                    'role': 'tool',
                    'tool_call_id': tc.id,
                    'name': tool_name,
                    'content': tool_result,
                })
            continue

        break

    if not final_text.strip():
        final_text = 'I could not generate a response. Please try again.'

    return final_text.strip(), messages


def _execute_tool(name, args, user):
    """Execute a tool function and return its output as a string."""
    tool_map = get_tools()
    if name not in tool_map:
        return f'Error: Unknown tool "{name}"'

    func = tool_map[name]['code']
    try:
        if name == 'get_overview':
            result = func(user)
        elif name == 'get_projects':
            result = func(user)
        elif name == 'get_tasks':
            status = args.get('status')
            result = func(user, status=status)
        elif name == 'get_users':
            result = func()
        else:
            result = f'Error: Tool "{name}" not implemented'
        return json.dumps({'result': str(result)})
    except Exception as e:
        return json.dumps({'error': f'Error executing tool "{name}": {str(e)}'})


def _sse_generator(request, session, user_chat_message):
    """Generate SSE events for streaming the chat response."""
    user_message = user_chat_message.content
    messages = list(
        session.messages.filter(created_at__lt=user_chat_message.created_at)
        .order_by('created_at')
    )
    history = [{'role': m.role, 'content': m.content} for m in messages]

    # Send initial event
    yield f'data: {json.dumps({"type": "start", "message": "Thinking..."})}\n\n'

    try:
        response_text, final_history = _run_react_loop(
            request.user, user_message, history
        )

        # Stream fixed-size text chunks so whitespace is preserved.
        chunk_size = 80
        for i in range(0, len(response_text), chunk_size):
            chunk = response_text[i:i + chunk_size]
            yield f'data: {json.dumps({"type": "message_chunk", "text": chunk})}\n\n'
            time.sleep(0.05)

        full_response = response_text
        ChatMessage.objects.create(session=session, role='assistant', content=full_response)

    except Exception as e:
        yield f'data: {json.dumps({"type": "error", "message": str(e)})}\n\n'

    yield f'data: {json.dumps({"type": "done"})}\n\n'


@login_required
def chat_page(request):
    """Render the chat page."""
    return render(request, 'chatbot/chat.html')


@login_required
def chat_stream(request):
    """SSE endpoint for streaming chat responses."""
    if request.method != 'GET':
        return JsonResponse({'error': 'GET only'}, status=405)

    session_id = request.GET.get('session_id')
    if not session_id:
        return JsonResponse({'error': 'session_id required'}, status=400)

    message_id = request.GET.get('message_id')
    if not message_id:
        return JsonResponse({'error': 'message_id required'}, status=400)

    session = get_object_or_404(ChatSession, pk=session_id, user=request.user)
    user_chat_message = get_object_or_404(
        ChatMessage,
        pk=message_id,
        session=session,
        role='user',
    )

    response = StreamingHttpResponse(
        _sse_generator(request, session, user_chat_message),
        content_type='text/event-stream',
    )
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response


@login_required
@require_POST
def chat_send(request):
    """Handle a chat message send. Returns the session_id to poll via SSE."""
    session_id = request.POST.get('session_id')
    message = request.POST.get('message', '').strip()

    if not message:
        return JsonResponse({'error': 'Empty message'}, status=400)

    if not session_id:
        return JsonResponse({'error': 'session_id required'}, status=400)

    session = get_object_or_404(ChatSession, pk=session_id, user=request.user)
    chat_message = ChatMessage.objects.create(
        session=session,
        role='user',
        content=message,
    )

    return JsonResponse({
        'session_id': str(session.pk),
        'message_id': str(chat_message.pk),
        'status': 'ready',
    })


@login_required
def session_messages(request, pk):
    """Return JSON messages for a chat session."""
    session = get_object_or_404(ChatSession, pk=pk, user=request.user)
    messages = session.messages.all().order_by('created_at')
    data = [
        {
            'pk': str(m.pk),
            'role': m.role,
            'content': m.content,
            'created_at': m.created_at.isoformat(),
        }
        for m in messages
    ]
    return JsonResponse(data, safe=False)


@login_required
def session_list(request):
    """Return JSON list of user's active sessions."""
    sessions = ChatSession.objects.filter(
        user=request.user, is_active=True
    ).order_by('-created_at')
    data = [
        {
            'pk': str(s.pk),
            'title': s.title,
            'created_at': s.created_at.isoformat(),
        }
        for s in sessions
    ]
    return JsonResponse(data, safe=False)


@login_required
@require_POST
def session_new(request):
    """Create a new chat session."""
    title = request.POST.get('title', 'New Chat')
    session = ChatSession.objects.create(
        user=request.user,
        title=title,
    )
    return JsonResponse({
        'pk': str(session.pk),
        'title': session.title,
        'created_at': session.created_at.isoformat(),
    })


@login_required
@require_POST
def session_delete(request, pk):
    """Delete (deactivate) a chat session."""
    session = get_object_or_404(ChatSession, pk=pk, user=request.user)
    session.is_active = False
    session.save()
    return JsonResponse({'status': 'deleted'})
