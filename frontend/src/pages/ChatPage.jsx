import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Header from '../components/layout/Header';
import UploadDocumentPage from '../pages/UploadDocumentPage';
import { getAccessToken } from '../assets/auth';
import { useParams } from 'react-router-dom';

export default function ChatPage() {
  const { chatId } = useParams();   // from route /chats/:chatId
  const [messages, setMessages] = useState([]);
  const [docs,     setDocs]     = useState([]);
  const [isTyping, setIsTyping] = useState(false);
  const [input, setInput] = useState('');
  const [error, setError] = useState(null);

  // --- Nou: stări pentru quiz ---
  const [numQuestions, setNumQuestions] = useState(5);
  const [difficulty,  setDifficulty]   = useState('easy');
  const [quizQuestions, setQuizQuestions] = useState([]);

  const handleDocUploadSuccess = (doc) => {
    setDocs(prev => [doc, ...prev]);
  };
  
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

    // load documents for this chat
    (async () => {
      try {
        const token = await getAccessToken();
        const res = await axios.get(
          `http://localhost:8000/documents/?chat_id=${chatId}`,
          { headers: { Authorization: `Bearer ${token}` } }
        );
        setDocs(res.data);
      } catch (e) {
        console.error('Failed to load docs', e);
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

  //  generare quiz
  const handleGenerateQuiz = async (e) => {
    e.preventDefault();
    setError(null);
    try {
      const token = await getAccessToken();
      const res = await axios.post(
        `http://localhost:8000/chats/${chatId}/generate-quiz/`,
        { num_questions: numQuestions, difficulty },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setQuizQuestions(res.data.questions);
    } catch (e) {
      console.error(e);
      setError('Eroare la generarea quiz-ului.');
    }
  };


  return (
    <>
      <Header />
      <div style={{ marginTop: 60, padding: 20 }}>
        <div style={{ maxWidth: 600, margin: '0 auto' }}>
          <h2>Chat Room</h2>
          <div
            style={{
              border: '1px solid #ccc',
              borderRadius: 4,
              padding: 10,
              height: 400,
              overflowY: 'auto',
              background: '#f9f9f9'
            }}
          >
            {messages.map((m, i) => (
              <div
                key={i}
                style={{
                  textAlign: m.role === 'user' ? 'right' : 'left',
                  margin: '10px 0'
                }}
              >
                <span
                  style={{
                    display: 'inline-block',
                    padding: '8px 12px',
                    borderRadius: 16,
                    background: m.role === 'user' ? '#3A59D1' : '#7AC6D2',
                    color: '#fff'
                  }}
                >
                  {m.content}
                </span>
              </div>
            ))}
            {isTyping && (
              <div style={{ textAlign: 'left', margin: '10px 0' }}>
                <span
                  style={{
                    display: 'inline-block',
                    padding: '8px 12px',
                    borderRadius: 16,
                    background: '#7AC6D2',
                    color: '#fff',
                    fontStyle: 'italic',
                    opacity: 0.7
                  }}
                >
                  …
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
              style={{
                width: '80%',
                padding: 8,
                borderRadius: 4,
                border: '1px solid #ccc'
              }}
            />
            <button
              type="submit"
              style={{
                padding: '8px 12px',
                marginLeft: 8,
                background: '#3A59D1',
                color: '#fff',
                border: 'none',
                borderRadius: 4
              }}
            >
              Send
            </button>
          </form>
  
          <UploadDocumentPage
            chatId={chatId}
            onSuccess={handleDocUploadSuccess}
          />
  
          <div style={{ marginTop: 20 }}>
            {/* ————— Generare Quiz ————— */}
            <div style={{
                marginTop: 40,
                padding: 20,
                border: '1px solid #3A59D1',
                borderRadius: 8,
                background: '#f0f8ff'
            }}>
              <h3>Generează un Quiz</h3>
              <form onSubmit={handleGenerateQuiz}
                    style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                <div>
                  <label>Număr întrebări:</label><br/>
                  <input
                    type="number" min="1" max="20"
                    value={numQuestions}
                    onChange={e => setNumQuestions(e.target.value)}
                    style={{ width: 60, padding: 4 }}
                  />
                </div>
                <div>
                  <label>Dificultate:</label><br/>
                  <select
                    value={difficulty}
                    onChange={e => setDifficulty(e.target.value)}
                    style={{ padding: 4 }}
                  >
                    <option value="easy">Ușor</option>
                    <option value="medium">Mediu</option>
                    <option value="hard">Greu</option>
                  </select>
                </div>
                <button type="submit" style={{
                  padding: '8px 12px',
                  background: '#3A59D1',
                  color: '#fff',
                  border: 'none',
                  borderRadius: 4
                }}>
                  Generează
                </button>
              </form>
              {error && <p style={{ color: 'red' }}>{error}</p>}

              {quizQuestions.length > 0 && (
                <div style={{ marginTop: 20 }}>
                  <h4>Întrebările Quiz-ului:</h4>
                  <ol>
                    {quizQuestions.map(q => (
                      <li key={q.id} style={{ marginBottom: 10 }}>
                        <strong>{q.question}</strong>
                        <ul>
                          {q.options.map((opt, i) => <li key={i}>{opt}</li>)}
                        </ul>
                      </li>
                    ))}
                  </ol>
                </div>
              )}
            </div>
            {/* —————————————————————— */}

            <h3>Uploaded Documents</h3>
            {docs.length === 0 ? (
              <p style={{ fontStyle: 'italic' }}>No documents yet</p>
            ) : (
              docs.map(d => (
                <div
                  key={d.id}
                  style={{
                    padding: '8px',
                    border: '1px solid #ccc',
                    borderRadius: 4,
                    marginBottom: 8
                  }}
                >
                  <a
                    href={`http://localhost:8000${d.file}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{ color: '#3A59D1', textDecoration: 'none' }}
                  >
                    {d.name}
                  </a>
                  <span style={{ float: 'right', color: '#555' }}>
                    {new Date(d.uploaded_at).toLocaleDateString()}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </>
  );  
}
