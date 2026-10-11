import { useState, useEffect } from 'react';
import { getChatConfig } from '../../config/configLoader';

export const useMessages = () => {
  const [initialMessage, setInitialMessage] = useState({ 
    role: 'assistant', 
    content: 'Loading...'
  });
  
  const [messages, setMessages] = useState([]);
  
  // Load the initial message from the configuration
  useEffect(() => {
    const chatConfig = getChatConfig();
    const initialMessage = chatConfig?.initialMessage || 'Hello! How can I help you today?';
    
    const message = { 
      role: 'assistant', 
      content: initialMessage
    };
    
    setInitialMessage(message);
    setMessages([message]);
  }, []);

  const addMessage = (message) => {
    setMessages(prev => [...prev, message]);
  };

const updateLastMessage = (content, isTyping = true, extra = {}) => {
  setMessages(prev => {
    const newMessages = [...prev];
    if (newMessages.length > 0) {
      const i = newMessages.length - 1;
      newMessages[i] = {
        ...newMessages[i],
        content,
        isTyping,
        ...extra
      };
    }
    return newMessages;
  });
};

  const resetMessages = () => {
    setMessages([initialMessage]);
  };

  return {
    messages,
    addMessage,
    updateLastMessage,
    resetMessages
  };
}; 