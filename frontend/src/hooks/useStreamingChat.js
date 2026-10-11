import { useState, useCallback, useRef } from 'react'
import { useSession } from './chat/useSession'
import { useMessages } from './chat/useMessages'
import { ChatService } from '../services/chatService'

export const useStreamingChat = () => {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const [messageCount, setMessageCount] = useState(0)
  const [messageLimit, setMessageLimit] = useState(8)

  const { sessionId, updateSessionId, startNewSession } = useSession()
  const { messages, addMessage, resetMessages, updateLastMessage } = useMessages()
  const shouldStopRef = useRef(false)
  const requestInProgressRef = useRef(false)

  const stopAnswering = useCallback(() => {
    shouldStopRef.current = true
  }, [])
const sendMessage = async (chatRequest) => {
  if (requestInProgressRef.current) return;

  requestInProgressRef.current = true;
  shouldStopRef.current = false;
  setIsLoading(true);
  setError(null);

  try {
    addMessage({ role: 'user', content: chatRequest.message });
    addMessage({ role: 'assistant', content: '', isTyping: true, sources: [] });

    const slug = import.meta.env.VITE_CHATBOT_SLUG;
    if (!slug) throw new Error('VITE_CHATBOT_SLUG is not configured');

    let answer = '';

    const response = await ChatService.sendMessage(
      chatRequest.message,
      sessionId,
      slug,
      (token) => {
        if (shouldStopRef.current) return;
        answer += token;
        updateLastMessage(answer);
      }
    );

    if (response.session_id) updateSessionId(response.session_id);

    setMessageCount(response.message_count);
    setMessageLimit(response.message_limit);

   updateLastMessage(response.answer, false, {
  sources: response.sources || []
});
  } catch (err) {
    setError(err.message);
  } finally {
    requestInProgressRef.current = false;
    setIsLoading(false);
  }
};

  const startNewChat = useCallback(() => {
    startNewSession()
    resetMessages()
    setMessageCount(0)
    setError(null)
    shouldStopRef.current = false
  }, [startNewSession, resetMessages])

  return {
    messages,
    isLoading,
    error,
    sendMessage,
    sessionId,
    startNewChat,
    stopAnswering,
    messageCount,
    messageLimit
  }
}