// src/pages/ChatPage.jsx

import React, { useState, useEffect } from "react";
import axios from "axios";
import Header from "../components/layout/Header";
import UploadDocumentPage from "../pages/UploadDocumentPage";
import { getAccessToken } from "../assets/auth";
import { useParams } from "react-router-dom";

export default function ChatPage() {
  const { chatId } = useParams();

  const [messages, setMessages]       = useState([]);
  const [docs, setDocs]               = useState([]);
  const [isTyping, setIsTyping]       = useState(false);
  const [input, setInput]             = useState("");
  const [error, setError]             = useState(null);

  // ––– Quiz state –––
  const [numQuestions, setNumQuestions]       = useState(5);
  const [difficulty, setDifficulty]           = useState("easy");
  const [quizQuestions, setQuizQuestions]     = useState([]); 
  const [selectedAnswers, setSelectedAnswers] = useState({}); 
  const [savedQuizPath, setSavedQuizPath]     = useState(null);

  // ––– Whenever a new document is uploaded, prepend it –––
  const handleDocUploadSuccess = (doc) => {
    setDocs((prev) => [doc, ...prev]);
  };

  // ––– On mount: fetch existing messages & docs –––
  useEffect(() => {
    (async () => {
      try {
        const token = await getAccessToken();
        const res = await axios.get(
          `http://localhost:8000/api/chats/${chatId}/messages/`,
          { headers: { Authorization: `Bearer ${token}` } }
        );
        setMessages(res.data);
      } catch (e) {
        console.error(e);
      }
    })();

    (async () => {
      try {
        const token = await getAccessToken();
        const res = await axios.get(
          `http://localhost:8000/api/documents/?chat_id=${chatId}`,
          { headers: { Authorization: `Bearer ${token}` } }
        );
        setDocs(res.data);
      } catch (e) {
        console.error("Failed to load docs", e);
      }
    })();
  }, [chatId]);

  // ––– Standard “send user message to chat” –––
  const sendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;
    setError(null);

    const userMsg = { role: "user", content: input };
    setMessages((m) => [...m, userMsg]);
    setInput("");
    setIsTyping(true);

    try {
      const token = await getAccessToken();
      const res = await axios.post(
        `http://localhost:8000/api/chats/${chatId}/messages/`,
        { message: input },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      const cleanReply = res.data.reply.replace(
        /<think>[\s\S]*?<\/think>/gi,
        ""
      ).trim();

      setIsTyping(false);
      setMessages((m) => [...m, { role: "assistant", content: cleanReply }]);
    } catch (e) {
      setIsTyping(false);
      console.error(e);
      setError("Failed to get reply. Try again.");
    }
  };

  // ––– Generate quiz via LLM –––
  const handleGenerateQuiz = async (e) => {
    e.preventDefault();
    setError(null);

    try {
      const token = await getAccessToken();
      const res = await axios.post(
        `http://localhost:8000/api/chats/${chatId}/generate-quiz/`,
        { num_questions: numQuestions, difficulty },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      // res.data is the serialized ChatMessage that the backend created:
      //    { id: 123, role: "assistant", content: "<JSON string>", timestamp: "…" }
      const quizJsonString = res.data.content;

      let parsed = null;
      try {
        parsed = JSON.parse(quizJsonString);
      } catch (parseErr) {
        console.error("Error parsing quiz JSON:", parseErr);
        setError("Failed to parse quiz data.");
        return;
      }

      // Normalize into an array of question‐objects:
      let questionArray = [];
      if (Array.isArray(parsed)) {
        questionArray = parsed;
      } else if (parsed && typeof parsed === "object" && Array.isArray(parsed.quiz)) {
        questionArray = parsed.quiz;
      } else if (parsed && typeof parsed === "object" && parsed.question) {
        questionArray = [parsed];
      } else {
        console.error("Unexpected quiz format:", parsed);
        setError("Unexpected quiz format.");
        return;
      }

      const normalized = questionArray.map((qObj) => ({
        question: qObj.question ?? "No question text",
        options: Array.isArray(qObj.options) ? qObj.options : [],
      }));

      // 1) Push the raw JSON bubble into chat history:
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: quizJsonString },
      ]);

      // 2) Store the parsed array for radio buttons, etc.
      setQuizQuestions(normalized);
      setSelectedAnswers({});
      setSavedQuizPath(null);
    } catch (e) {
      console.error(e);
      setError("Eroare la generarea quiz-ului.");
    }
  };

  // ––– When user picks an option for question index –––
  const handleOptionChange = (index, optionValue) => {
    setSelectedAnswers((prev) => ({
      ...prev,
      [index]: optionValue,
    }));
  };

  // ––– “Confirmă răspunsurile” –––
  const handleSubmitQuiz = async () => {
    setError(null);
    if (Object.keys(selectedAnswers).length !== quizQuestions.length) {
      setError("Please answer all questions before submitting.");
      return;
    }

    const payload = {
      quiz: quizQuestions,
      answers: selectedAnswers,
    };

    try {
      const token = await getAccessToken();
      const res = await axios.post(
        `http://localhost:8000/api/chats/${chatId}/submit-quiz/`,
        payload,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setSavedQuizPath(res.data.saved_path);
    } catch (e) {
      console.error("Error submitting quiz:", e.response || e.message);
      setError("Eroare la trimiterea răspunsurilor.");
    }
  };

  // ––– NEW: “Tips & Tricks” –––
  const handleGetTips = async () => {
    setError(null);

    if (quizQuestions.length === 0) {
      setError("Mai întâi generează și confirmă răspunsurile quiz-ului.");
      return;
    }
    if (Object.keys(selectedAnswers).length !== quizQuestions.length) {
      setError("Trebuie să confirmi toate răspunsurile înainte să primești sfaturi.");
      return;
    }

    const payload = {
      quiz: quizQuestions,
      answers: selectedAnswers,
    };

    try {
      const token = await getAccessToken();
      const res = await axios.post(
        `http://localhost:8000/api/chats/${chatId}/quiz-tips/`,
        payload,
        { headers: { Authorization: `Bearer ${token}` } }
      );

      // Backend returns the new ChatMessage:
      // { id: 456, role: "assistant", content: "<tips text>", timestamp: "…" }
      const tipMsg = res.data;
      setMessages((prev) => [...prev, { role: tipMsg.role, content: tipMsg.content }]);
    } catch (e) {
      console.error("Error fetching tips:", e.response || e.message);
      setError("Eroare la generarea sfaturilor.");
    }
  };

  return (
    <>
      <Header />
      <div style={{ marginTop: 60, padding: 20 }}>
        <div style={{ maxWidth: 600, margin: "0 auto" }}>
          <h2>Chat Room</h2>
          <div
            style={{
              border: "1px solid #ccc",
              borderRadius: 4,
              padding: 10,
              height: 400,
              overflowY: "auto",
              background: "#f9f9f9",
            }}
          >
            {messages.map((m, i) => (
              <div
                key={i}
                style={{
                  textAlign: m.role === "user" ? "right" : "left",
                  margin: "10px 0",
                }}
              >
                <span
                  style={{
                    display: "inline-block",
                    padding: "8px 12px",
                    borderRadius: 16,
                    background: m.role === "user" ? "#3A59D1" : "#7AC6D2",
                    color: "#fff",
                  }}
                >
                  {m.content}
                </span>
              </div>
            ))}
            {isTyping && (
              <div style={{ textAlign: "left", margin: "10px 0" }}>
                <span
                  style={{
                    display: "inline-block",
                    padding: "8px 12px",
                    borderRadius: 16,
                    background: "#7AC6D2",
                    color: "#fff",
                    fontStyle: "italic",
                    opacity: 0.7,
                  }}
                >
                  …
                </span>
              </div>
            )}
          </div>

          {error && <p style={{ color: "red" }}>{error}</p>}

          <form onSubmit={sendMessage} style={{ marginTop: 10 }}>
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type a message…"
              style={{
                width: "80%",
                padding: 8,
                borderRadius: 4,
                border: "1px solid #ccc",
              }}
            />
            <button
              type="submit"
              style={{
                padding: "8px 12px",
                marginLeft: 8,
                background: "#3A59D1",
                color: "#fff",
                border: "none",
                borderRadius: 4,
              }}
            >
              Send
            </button>
          </form>

          <UploadDocumentPage
            chatId={chatId}
            onSuccess={handleDocUploadSuccess}
          />

          {/* ───── Quiz generation UI ───── */}
          <div
            style={{
              marginTop: 40,
              padding: 20,
              border: "1px solid #3A59D1",
              borderRadius: 8,
              background: "#f0f8ff",
            }}
          >
            <h3>Generează un Quiz</h3>
            <form
              onSubmit={handleGenerateQuiz}
              style={{ display: "flex", gap: "10px", alignItems: "center" }}
            >
              <div>
                <label>Număr întrebări:</label>
                <br />
                <input
                  type="number"
                  min="1"
                  max="20"
                  value={numQuestions}
                  onChange={(e) => setNumQuestions(e.target.value)}
                  style={{ width: 60, padding: 4 }}
                />
              </div>
              <div>
                <label>Dificultate:</label>
                <br />
                <select
                  value={difficulty}
                  onChange={(e) => setDifficulty(e.target.value)}
                  style={{ padding: 4 }}
                >
                  <option value="easy">Ușor</option>
                  <option value="medium">Mediu</option>
                  <option value="hard">Greu</option>
                </select>
              </div>
              <button
                type="submit"
                style={{
                  padding: "8px 12px",
                  background: "#3A59D1",
                  color: "#fff",
                  border: "none",
                  borderRadius: 4,
                }}
              >
                Generează
              </button>
            </form>

            {quizQuestions.length > 0 && (
              <div style={{ marginTop: 20 }}>
                <h4>Întrebările Quiz-ului:</h4>
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    handleSubmitQuiz();
                  }}
                >
                  <ol>
                    {quizQuestions.map((q, index) => (
                      <li key={index} style={{ marginBottom: 10 }}>
                        <strong>{q.question}</strong>
                        <br />
                        {q.options.map((opt, i) => (
                          <label
                            key={i}
                            style={{ display: "block", marginTop: 4 }}
                          >
                            <input
                              type="radio"
                              name={`question_${index}`}
                              value={opt}
                              checked={selectedAnswers[index] === opt}
                              onChange={() =>
                                handleOptionChange(index, opt)
                              }
                              style={{ marginRight: 6 }}
                            />
                            {opt}
                          </label>
                        ))}
                      </li>
                    ))}
                  </ol>
                  <button
                    type="submit"
                    style={{
                      marginTop: 12,
                      backgroundColor: "#28a745",
                      color: "#fff",
                      padding: "8px 16px",
                      border: "none",
                      borderRadius: 4,
                      fontSize: "1rem",
                      cursor: "pointer",
                    }}
                  >
                    Confirmă răspunsurile
                  </button>
                </form>

                {savedQuizPath && (
                  <div style={{ marginTop: 10 }}>
                    <p>Răspunsurile au fost salvate!</p>
                    <a
                      href={savedQuizPath}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{ color: "#3A59D1", textDecoration: "underline" }}
                    >
                      Descarcă fișierul quiz
                    </a>

                    {/* ── NEW: Tips & Tricks button appears once quiz is submitted ── */}
                    <button
                      onClick={handleGetTips}
                      style={{
                        display: "block",
                        marginTop: 12,
                        backgroundColor: "#ffc107",
                        color: "#000",
                        padding: "8px 16px",
                        border: "none",
                        borderRadius: 4,
                        fontSize: "1rem",
                        cursor: "pointer",
                      }}
                    >
                      Sfaturi și trucuri
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
          {/* ──────────────────────────────── */}

          <h3>Uploaded Documents</h3>
          {docs.length === 0 ? (
            <p style={{ fontStyle: "italic" }}>No documents yet</p>
          ) : (
            docs.map((d) => (
              <div
                key={d.id}
                style={{
                  padding: "8px",
                  border: "1px solid #ccc",
                  borderRadius: 4,
                  marginBottom: 8,
                }}
              >
                <a
                  href={`http://localhost:8000${d.file}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{ color: "#3A59D1", textDecoration: "none" }}
                >
                  {d.name}
                </a>
                <span style={{ float: "right", color: "#555" }}>
                  {new Date(d.uploaded_at).toLocaleDateString()}
                </span>
              </div>
            ))
          )}
        </div>
      </div>
    </>
  );
}
