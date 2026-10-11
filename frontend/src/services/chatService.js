const BACKEND_URL =
  import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

export class ChatService {
//   static async sendMessage(message, sessionId, slug) {
//     const response = await fetch(
//       `${BACKEND_URL}/chat/${encodeURIComponent(slug)}`,
//       {
//         method: 'POST',
//         headers: {
//           'Content-Type': 'application/json',
//         },
//         body: JSON.stringify({
//           message,
//           session_id: sessionId || null,
//         }),
//       }
//     );

//     const text = await response.text();

//     if (!response.ok) {
//       throw new Error(
//         `Backend error (${response.status}): ${text || 'empty response'}`
//       );
//     }

//     if (!text) {
//       throw new Error('Backend returned an empty response');
//     }

//     try {
//       return JSON.parse(text);
//     } catch {
//       throw new Error(
//         `Backend returned invalid JSON: ${text.slice(0, 200)}`
//       );
//     }
//   }
// }

static async sendMessage(message, sessionId, slug, onToken) {

  const response = await fetch(
    `${BACKEND_URL}/chat/${encodeURIComponent(slug)}`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message,
        session_id: sessionId || null,
      }),
    }
  );

  if (!response.ok) {
    throw new Error(`Backend error (${response.status})`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let result = null;

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const events = buffer.split('\n\n');
    buffer = events.pop();

    for (const event of events) {
      const line = event.split('\n').find(line => line.startsWith('data: '));
      if (!line) continue;

      const data = JSON.parse(line.slice(6));

      if (data.type === 'token') {
        onToken?.(data.text);

      } 
      if (data.type === 'error') {
      throw new Error(data.message);
      }else if (data.type === 'done') {
        result = data;
      }
    }
  }

  if (!result) throw new Error('Stream ended without a final event');
  return result;
}
}