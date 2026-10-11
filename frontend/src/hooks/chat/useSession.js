import { useState, useCallback } from 'react';

export const useSession = () => {
  const chatbotSlug = import.meta.env.VITE_CHATBOT_SLUG;
  const storageKey = `chatSessionId_${chatbotSlug || 'default'}`;

  const [sessionId, setSessionId] = useState(
    () => localStorage.getItem(storageKey)
  );

  const updateSessionId = useCallback((newSessionId) => {
    if (!newSessionId) return;

    localStorage.setItem(storageKey, newSessionId);
    setSessionId(newSessionId);
  }, [storageKey]);

  const startNewSession = useCallback(() => {
    localStorage.removeItem(storageKey);
    setSessionId(null);
  }, [storageKey]);

  return { sessionId, updateSessionId, startNewSession };
};