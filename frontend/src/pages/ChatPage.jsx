import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Header from '../components/layout/Header';
import { getAccessToken } from '../assets/auth';
import { useParams } from 'react-router-dom';

export default function ChatPage() {
  const { chatId } = useParams();   // from route /chats/:chatId
  const [messages, setMessages] = useState([]);
  const [isTyping, setIsTyping] = useState(false);
  const [input, setInput] = useState('');
  const [error, setError] = useState(null);

  useEffect(() => {
    // Fetch existing messages
    (async () => {
      try {
        const token = await getAccessToken();
        const res = await axios.get(
          `http://localhost:8000/chats/${chatId}/messages/`,
          { headers: { Authorization: `Bearer ${token}` } }
        );
        setMessages(res.data);
      } catch (e) {
        console.error(e);
      }
    })();
  }, [chatId]);

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;
    setError(null);

    // Optimistically show the user's message
    const userMsg = { role: 'user', content: input };
    setMessages((m) => [...m, userMsg]);
    setInput('');

    setIsTyping(true); 

    try {
      const token = await getAccessToken();
      const res = await axios.post(
        `http://localhost:8000/chats/${chatId}/messages/`,
        { message: input },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      res.data.reply = res.data.reply
    .replace(/<think>[\s\S]*?<\/think>/gi, '')
    .trim();

        setIsTyping(false); 
      const assistantMsg = { role: 'assistant', content: res.data.reply };
      setMessages((m) => [...m, assistantMsg]);
    } catch (e) {
        setIsTyping(false); 
      console.error(e);
      setError('Failed to get reply. Try again.');
    }
  };

  return (
    <>
      <Header />
      <div style={{ marginTop: 60, padding: 20 }}>
        <div style={{ maxWidth: 600, margin: '0 auto' }}>
          <h2>Chat Room</h2>
          <div style={{
            border: '1px solid #ccc',
            borderRadius: 4,
            padding: 10,
            height: 400,
            overflowY: 'auto',
            background: '#f9f9f9'
          }}>
            {messages.map((m, i) => (
              <div key={i} style={{
                textAlign: m.role === 'user' ? 'right' : 'left',
                margin: '10px 0'
              }}>
                <span style={{
                  display: 'inline-block',
                  padding: '8px 12px',
                  borderRadius: 16,
                  background: m.role === 'user' ? '#3A59D1' : '#7AC6D2',
                  color: '#fff',
                }}>
                  {m.content}
                </span>
              </div>
            ))}
           {isTyping && (                                        // ← ADDED
             <div style={{ textAlign: 'left', margin: '10px 0' }}>
               <span style={{
                 display: 'inline-block',
                 padding: '8px 12px',
                 borderRadius: 16,
                 background: '#7AC6D2',
                 color: '#fff',
                 fontStyle: 'italic',
                 opacity: 0.7
               }}>
                 …{/* simple dots indicator */}
               </span>
             </div>
           )}  
          </div>
          {error && <p style={{ color: 'red' }}>{error}</p>}
          <form onSubmit={sendMessage} style={{ marginTop: 10 }}>
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type a message…"
              style={{ width: '80%', padding: 8, borderRadius: 4, border: '1px solid #ccc' }}
            />
            <button type="submit" style={{
              padding: '8px 12px', marginLeft: 8,
              background: '#3A59D1', color: '#fff', border: 'none', borderRadius: 4
            }}>
              Send
            </button>
          </form>
        </div>
      </div>
    </>
  );
}
