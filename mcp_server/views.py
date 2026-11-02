"""Minimal MCP streamable HTTP endpoint (JSON responses, no SSE stream).

Implements the legacy ``initialize`` handshake plus tools, resources, and
prompts listing so the official ``mcp`` Python SDK client can connect.
"""
import json
import logging
import traceback
import uuid

from django.contrib.auth.models import AnonymousUser, User
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from mcp_server.tools import RESOURCES, TOOLS, ToolInputError

logger = logging.getLogger(__name__)

SUPPORTED_PROTOCOL_VERSIONS = ('2024-11-05', '2025-03-26', '2025-06-18', '2025-11-25')
SERVER_INFO = {'name': 'vtm-mcp', 'version': '1.0.0'}

PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603


def _authenticate(request):
    # VULN (fail-open auth): a missing or invalid bearer token is not rejected;
    # the request simply continues as an anonymous user.
    header = request.META.get('HTTP_AUTHORIZATION', '')
    if not header.lower().startswith('bearer '):
        return AnonymousUser()
    token = header[7:].strip()

    from rest_framework.authtoken.models import Token
    match = Token.objects.select_related('user').filter(key=token).first()
    if match:
        return match.user

    from rest_framework_simplejwt.tokens import AccessToken
    try:
        return User.objects.get(pk=AccessToken(token)['user_id'])
    except Exception:
        return AnonymousUser()


def _result(msg_id, result):
    return {'jsonrpc': '2.0', 'id': msg_id, 'result': result}


def _error(msg_id, code, message, data=None):
    error = {'code': code, 'message': message}
    if data is not None:
        error['data'] = data
    return {'jsonrpc': '2.0', 'id': msg_id, 'error': error}


def _text_result(text, is_error=False):
    result = {'content': [{'type': 'text', 'text': text}]}
    if is_error:
        result['isError'] = True
    return result


def _initialize(params):
    requested = params.get('protocolVersion')
    version = requested if requested in SUPPORTED_PROTOCOL_VERSIONS else SUPPORTED_PROTOCOL_VERSIONS[-1]
    return {
        'protocolVersion': version,
        'capabilities': {'tools': {}, 'resources': {}, 'prompts': {}},
        'serverInfo': SERVER_INFO,
        'instructions': 'VTM task manager tools for projects, tasks, notes, and users.',
    }


def _list_tools():
    return {'tools': [
        {'name': name, 'description': tool['description'], 'inputSchema': tool['inputSchema']}
        for name, tool in TOOLS.items()
    ]}


def _call_tool(user, params):
    name = params.get('name')
    tool = TOOLS.get(name)
    if tool is None:
        raise _RpcError(INVALID_PARAMS, f'Unknown tool: {name}')
    arguments = params.get('arguments') or {}
    if not isinstance(arguments, dict):
        raise _RpcError(INVALID_PARAMS, 'arguments must be an object')
    try:
        return _text_result(str(tool['code'](user, arguments)))
    except ToolInputError as exc:
        return _text_result(str(exc), is_error=True)
    except ObjectDoesNotExist as exc:
        return _text_result(f'Not found: {exc}', is_error=True)


def _list_resources():
    return {'resources': [
        {'uri': uri, 'name': res['name'], 'description': res['description'], 'mimeType': res['mimeType']}
        for uri, res in RESOURCES.items()
    ]}


def _read_resource(params):
    uri = params.get('uri')
    resource = RESOURCES.get(uri)
    if resource is None:
        raise _RpcError(INVALID_PARAMS, f'Unknown resource: {uri}')
    return {'contents': [{'uri': uri, 'mimeType': resource['mimeType'], 'text': resource['code']()}]}


class _RpcError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


def _dispatch(user, message):
    method = message.get('method')
    params = message.get('params') or {}
    if not isinstance(params, dict):
        raise _RpcError(INVALID_PARAMS, 'params must be an object')
    if method == 'initialize':
        return _initialize(params)
    if method == 'ping':
        return {}
    if method == 'tools/list':
        return _list_tools()
    if method == 'tools/call':
        return _call_tool(user, params)
    if method == 'resources/list':
        return _list_resources()
    if method == 'resources/templates/list':
        return {'resourceTemplates': []}
    if method == 'resources/read':
        return _read_resource(params)
    if method == 'prompts/list':
        return {'prompts': []}
    raise _RpcError(METHOD_NOT_FOUND, f'Method not found: {method}')


def _handle_message(user, message):
    if not isinstance(message, dict) or message.get('jsonrpc') != '2.0' or 'method' not in message:
        return _error(message.get('id') if isinstance(message, dict) else None, INVALID_REQUEST, 'Invalid Request')
    if 'id' not in message:
        return None  # notification
    msg_id = message['id']
    try:
        return _result(msg_id, _dispatch(user, message))
    except _RpcError as exc:
        return _error(msg_id, exc.code, exc.message)
    except Exception as exc:
        # VULN (error disclosure): unhandled exceptions return the full
        # traceback, file paths, and exception text to the client.
        tb = traceback.format_exc()
        logger.exception('MCP request failed')
        return _error(msg_id, INTERNAL_ERROR, f'{type(exc).__name__}: {exc}\n{tb}', {'traceback': tb})


@csrf_exempt
def mcp_endpoint(request):
    if request.method == 'DELETE':
        return HttpResponse(status=200)
    if request.method != 'POST':
        return HttpResponse(status=405, headers={'Allow': 'POST, DELETE'})

    try:
        payload = json.loads(request.body or b'')
    except ValueError:
        return JsonResponse(_error(None, PARSE_ERROR, 'Parse error'), status=400)

    if not isinstance(payload, dict):
        # JSON-RPC batching was removed from MCP in 2025-06-18.
        return JsonResponse(_error(None, INVALID_REQUEST, 'Invalid Request'), status=400)

    user = _authenticate(request)
    response = _handle_message(user, payload)
    if response is None:
        return HttpResponse(status=202)

    http_response = JsonResponse(response)
    if payload.get('method') == 'initialize':
        http_response['Mcp-Session-Id'] = uuid.uuid4().hex
    return http_response
