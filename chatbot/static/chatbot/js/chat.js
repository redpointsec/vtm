(function () {
  'use strict';

  var currentSessionId = null;
  var isStreaming = false;
  var abortController = null;

  // --- Session management ---

  function loadSessions() {
    fetch('/chat/sessions/')
      .then(function (r) { return r.json(); })
      .then(function (sessions) {
        var list = document.getElementById('session-list');
        list.innerHTML = '';
        sessions.forEach(function (s) {
          list.appendChild(createSessionItem(s));
        });
        if (sessions.length > 0 && !currentSessionId) {
          selectSession(sessions[0].pk);
        }
      });
  }

  function createSessionItem(session) {
    var li = document.createElement('li');
    li.className = 'chat-session-item' + (session.pk === currentSessionId ? ' active' : '');
    li.dataset.sessionId = session.pk;

    var titleSpan = document.createElement('span');
    titleSpan.className = 'session-title';
    titleSpan.textContent = session.title;

    var delBtn = document.createElement('button');
    delBtn.className = 'delete-session-btn';
    delBtn.dataset.sessionId = session.pk;
    delBtn.innerHTML = '<i class="fa fa-trash"></i>';
    delBtn.addEventListener('click', function (e) {
      e.stopPropagation();
      deleteSession(session.pk);
    });

    li.appendChild(titleSpan);
    li.appendChild(delBtn);
    li.addEventListener('click', function () { selectSession(session.pk); });

    return li;
  }

  function selectSession(id) {
    currentSessionId = id;
    document.querySelectorAll('.chat-session-item').forEach(function (li) {
      li.classList.toggle('active', li.dataset.sessionId === id);
    });
    loadMessages(id);
  }

  function createNewSession() {
    var formData = new FormData();
    formData.append('title', 'New Chat');
    fetch('/chat/session/new/', {
      method: 'POST',
      headers: { 'X-CSRFToken': getCookie('csrftoken') },
      body: formData,
    }).then(function (r) { return r.json(); }).then(function (session) {
      loadSessions();
      selectSession(session.pk);
    });
  }

  function deleteSession(id) {
    fetch('/chat/session/' + id + '/delete/', {
      method: 'POST',
      headers: { 'X-CSRFToken': getCookie('csrftoken') },
    }).then(function () {
      if (currentSessionId === id) {
        currentSessionId = null;
        document.getElementById('chat-messages').innerHTML =
          '<div class="chat-welcome"><p>Ask me about your projects, tasks, or users.</p></div>';
      }
      loadSessions();
    });
  }

  // --- Message display ---

  function loadMessages(sessionId) {
    var container = document.getElementById('chat-messages');
    container.innerHTML = '<div class="chat-welcome"><p>Loading chat history...</p></div>';

    fetch('/chat/session/' + encodeURIComponent(sessionId) + '/messages/')
      .then(function (r) { return r.json(); })
      .then(function (messages) {
        container.innerHTML = '';
        if (!messages.length) {
          container.innerHTML = '<div class="chat-welcome"><p>Ask me about your projects, tasks, or users.</p></div>';
          return;
        }
        messages.forEach(function (message) {
          appendMessage(message.role, message.content);
        });
      })
      .catch(function () {
        container.innerHTML = '<div class="chat-welcome"><p>Unable to load chat history.</p></div>';
      });
  }

  function appendMessage(role, text) {
    var container = document.getElementById('chat-messages');
    var welcome = container.querySelector('.chat-welcome');
    if (welcome) welcome.remove();

    var div = document.createElement('div');
    div.className = 'chat-message ' + (role === 'user' ? 'user-message' : 'assistant-message');

    var bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    bubble.innerHTML = formatMessage(text);

    div.appendChild(bubble);
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
    return div;
  }

  function appendThinkingMessage() {
    var messageEl = appendMessage('assistant', '');
    messageEl.classList.add('thinking');
    setMessageText(messageEl, '<span class="thinking-dots">...</span> Thinking');
    return messageEl;
  }

  function setMessageText(messageEl, html) {
    var bubble = messageEl.querySelector('.message-bubble');
    bubble.innerHTML = html;
    var container = document.getElementById('chat-messages');
    container.scrollTop = container.scrollHeight;
  }

  function formatMessage(text) {
    // Basic markdown-like formatting
    var html = text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/`(.+?)`/g, '<code>$1</code>')
      .replace(/\n/g, '<br>');
    return html;
  }

  function appendChunk(text, messageEl) {
    var bubble = messageEl.querySelector('.message-bubble');
    if (messageEl.classList.contains('thinking')) {
      messageEl.classList.remove('thinking');
      bubble.dataset.rawText = '';
    }

    var nextText = (bubble.dataset.rawText || '') + text;
    bubble.dataset.rawText = nextText;
    bubble.innerHTML = formatMessage(nextText);
    var container = document.getElementById('chat-messages');
    container.scrollTop = container.scrollHeight;
  }

  // --- Streaming ---

  function sendMessage() {
    if (isStreaming) return;

    var input = document.getElementById('chat-input');
    var text = input.value.trim();
    if (!text || !currentSessionId) return;

    input.value = '';
    appendMessage('user', text);
    isStreaming = true;

    var assistantMsg = appendThinkingMessage();

    // Save message via POST
    var formData = new FormData();
    formData.append('session_id', currentSessionId);
    formData.append('message', text);

    fetch('/chat/send/', {
      method: 'POST',
      headers: { 'X-CSRFToken': getCookie('csrftoken') },
      body: formData,
    }).then(function (r) { return r.json(); })
      .then(function (payload) {
        if (payload.error) {
          throw new Error(payload.error);
        }
        // Start SSE stream
        startStreaming(currentSessionId, payload.message_id, assistantMsg);
      })
      .catch(function (err) {
        isStreaming = false;
        assistantMsg.classList.remove('thinking');
        appendChunk('*Error sending message: ' + err.message + '*', assistantMsg);
      });
  }

  function startStreaming(sessionId, messageId, messageEl) {
    if (abortController) abortController.abort();
    abortController = new AbortController();

    fetch('/chat/stream/?session_id=' + encodeURIComponent(sessionId) + '&message_id=' + encodeURIComponent(messageId), {
      signal: abortController.signal,
    }).then(function (response) {
      if (!response.ok) {
        throw new Error('Stream request failed with HTTP ' + response.status);
      }
      var reader = response.body.getReader();
      var decoder = new TextDecoder();
      var buffer = '';

      function read() {
        reader.read().then(function ({ done, value }) {
          if (done) {
            isStreaming = false;
            abortController = null;
            // Update session title based on conversation
            updateSessionTitle(sessionId);
            return;
          }

          buffer += decoder.decode(value, { stream: true });
          var lines = buffer.split('\n');
          buffer = lines.pop();

          lines.forEach(function (line) {
            if (!line.startsWith('data: ')) return;
            try {
              var event = JSON.parse(line.slice(6));
              handleSSEEvent(event, messageEl);
            } catch (e) { /* skip malformed */ }
          });

          read();
        });
      }

      read();
    }).catch(function (err) {
      if (err.name !== 'AbortError') {
        isStreaming = false;
        messageEl.classList.remove('thinking');
        appendChunk('*Stream error: ' + err.message + '*', messageEl);
      }
    });
  }

  function handleSSEEvent(event, messageEl) {
    switch (event.type) {
      case 'start':
        setMessageText(messageEl, '<span class="thinking-dots">...</span> Thinking');
        break;
      case 'message_chunk':
        appendChunk(event.text, messageEl);
        break;
      case 'error':
        messageEl.classList.remove('thinking');
        appendChunk('*Error: ' + event.message + '*', messageEl);
        isStreaming = false;
        break;
      case 'done':
        if (messageEl.classList.contains('thinking')) {
          messageEl.classList.remove('thinking');
          setMessageText(messageEl, formatMessage('No response was returned.'));
        }
        isStreaming = false;
        abortController = null;
        updateSessionTitle(currentSessionId);
        break;
    }
  }

  function updateSessionTitle(sessionId) {
    // Don't update title for "New Chat" - keep it simple
    // In a future enhancement, we could ask the LLM to generate a title
  }

  // --- Utilities ---

  function getCookie(name) {
    var cookieValue = '';
    if (document.cookie) {
      var cookies = document.cookie.split(';');
      for (var i = 0; i < cookies.length; i++) {
        var cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  // --- Init ---

  document.getElementById('new-session-btn').addEventListener('click', createNewSession);
  document.getElementById('send-btn').addEventListener('click', sendMessage);
  document.getElementById('chat-input').addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  loadSessions();
})();
