import { Bot, User } from 'lucide-react';
import { motion } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import { RateLimitCountdown } from './RateLimitCountdown';
import { TypingIndicator } from './TypingIndicator';

export const ChatMessage = ({ message }) => {
  // If this is a typing message from the assistant with no content, render the standalone TypingIndicator
  if (message.role === 'assistant' && message.isTyping && !message.content) {
    return <TypingIndicator />;
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      transition={{ duration: 0.2 }}
      className="w-full"
    >
      <div className={`flex items-start gap-3 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
        {message.role === 'assistant' && <MessageAvatar icon={Bot} />}
        <div className={`flex flex-col ${message.role === 'user' ? 'items-end' : 'items-start'} max-w-[80%]`}>
          <MessageContent message={message} />
          {message.isError && message.retryAfter > 0 && (
            <RateLimitCountdown seconds={message.retryAfter} />
          )}
        </div>
        {message.role === 'user' && <MessageAvatar icon={User} />}
      </div>
    </motion.div>
  );
};

const MessageAvatar = ({ icon: Icon }) => (
  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-purple-500/20 flex items-center justify-center">
    <Icon className="w-4 h-4 text-purple-400" />
  </div>
);

const MessageContent = ({ message }) => (
  <div
    className={`rounded-2xl p-4 ${
      message.role === 'user'
        ? 'bg-purple-500 text-white'
        : message.isError
        ? 'bg-red-500/10 text-red-200 border border-red-500/20'
        : 'bg-gray-800/80 text-gray-200'
    } w-full`}
  >
    {message.role === 'user' ? (
      <UserMessage content={message.content} />
    ) : (
      <AssistantMessage message={message} />
    )}
  </div>
);

const UserMessage = ({ content }) => (
  <p className="leading-relaxed text-left whitespace-pre-wrap break-words">
    {content}
  </p>
);

const AssistantMessage = ({ message }) => (
  <div className="markdown-content w-full">
    <ReactMarkdown
      components={{
        p: 'p',
        h1: 'h1',
        h2: 'h2',
        h3: 'h3',
        ul: 'ul',
        ol: 'ol',
        li: 'li',
        code: 'code',
        pre: 'pre',
        blockquote: 'blockquote',
      }}
    >
      {message.content}
    </ReactMarkdown>

    {message.isTyping && <TypingIndicator inline />}

    <MessageSources sources={message.sources} />
  </div>
);

const MessageSources = ({ sources }) => {
  if (!Array.isArray(sources) || sources.length === 0) {
    return null;
  }

  // const uniqueSources = Array.from(
  //   new Map(
  //     sources.map((source) => [
  //       `${source.source}-${source.page_nr}`,
  //       source
  //     ])
  //   ).values()
  // );
const groupedSources = Object.values(
  sources.reduce((acc, source) => {
    const key = `${source.source}-${source.page_nr}`;

    if (!acc[key]) {
      acc[key] = {
        ...source,
        lines: [],
      };
    }

    if (source.lines) {
      acc[key].lines.push(source.lines);
    }


    return acc;
  }, {})
);

  return (
    <div className="mt-3 pt-3 border-t border-gray-700/50">
      <p className="text-xs text-gray-400 mb-2">
        Sources
      </p>

      <div className="flex flex-col gap-1">
        {/* {uniqueSources.map((source) => { */}
        {groupedSources.map((source) => {

          return (
            <a
              key={`${source.source}-${source.page}`}
              href={source.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-400 hover:underline break-words min-w-0"
            // >
            //   📄 {source.source} · p. {source.page} · l. {source.lines.join(', ')}
            // </a>
            >📄 {source.source} · p.{source.page}
{source.lines.length > 0 && (
  <>
    {' · l.'}
    {source.lines.slice(0, 3).join(', ')}
    {source.lines.length > 3 && '...'}
  </>
)}</a>
            
          );
        })}
      </div>
    </div>
  );
};