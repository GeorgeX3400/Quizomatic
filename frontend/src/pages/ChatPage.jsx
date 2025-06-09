// frontend/src/pages/ChatPage.jsx

import React, { useState, useEffect } from "react";
import axios from "axios";
import Header from "../components/layout/Header";
import UploadDocumentPage from "../pages/UploadDocumentPage";
import { getAccessToken } from "../assets/auth";
import { useParams } from "react-router-dom";
import "./ChatPage.css";

export default function ChatPage() {
  const { chatId } = useParams();

  const [messages, setMessages] = useState([]);
  const [docs, setDocs] = useState([]);
  const [isTyping, setIsTyping] = useState(false);
  const [input, setInput] = useState("");
  const [error, setError] = useState(null);

  // ─── Quiz state ─────────────
  const [numQuestions, setNumQuestions] = useState(5);
  const [difficulty, setDifficulty] = useState("easy");
  const [questionType, setQuestionType] = useState("multiple");
  const [quizQuestions, setQuizQuestions] = useState([]);
  const [selectedAnswers, setSelectedAnswers] = useState({});
  const [savedQuizPath, setSavedQuizPath] = useState(null);

  const handleDocUploadSuccess = (doc) => {
    setDocs((prev) => [doc, ...prev]);
  };

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
      const cleanReply = res.data.reply
        .replace(/<think>[\s\S]*?<\/think>/gi, "")
        .trim();

      setIsTyping(false);
      setMessages((m) => [
        ...m,
        { role: "assistant", content: cleanReply },
      ]);
    } catch (e) {
      setIsTyping(false);
      console.error(e);
      setError("Failed to get reply. Try again.");
    }
  };

  const handleGenerateQuiz = async (e) => {
    e.preventDefault();
    setError(null);

    try {
      const token = await getAccessToken();
      const res = await axios.post(
        `http://localhost:8000/api/chats/${chatId}/generate-quiz/`,
        {
          num_questions: numQuestions,
          difficulty,
          question_type: questionType,
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      const quizJsonString = res.data.content;
      let parsed = null;
      try {
        parsed = JSON.parse(quizJsonString);
      } catch (parseErr) {
        console.error("Error parsing quiz JSON:", parseErr);
        setError("Failed to parse quiz data.");
        return;
      }

      let questionArray = [];
      if (Array.isArray(parsed)) {
        questionArray = parsed;
      } else if (
        parsed &&
        typeof parsed === "object" &&
        Array.isArray(parsed.quiz)
      ) {
        questionArray = parsed.quiz;
      } else if (parsed && typeof parsed === "object" && parsed.question) {
        questionArray = [parsed];
      } else {
        console.error("Unexpected quiz format:", parsed);
        setError("Unexpected quiz format.");
        return;
      }

      const normalized = questionArray.map((qObj) => {
        if (Array.isArray(qObj.options)) {
          return {
            question: qObj.question ?? "No question text",
            options: qObj.options,
          };
        } else {
          return {
            question: qObj.question ?? "No question text",
            options: ["true", "false"],
          };
        }
      });

      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: quizJsonString },
      ]);
      setQuizQuestions(normalized);
      setSelectedAnswers({});
      setSavedQuizPath(null);
    } catch (e) {
      console.error(e);
      setError("Eroare la generarea quiz-ului.");
    }
  };

  const handleOptionChange = (index, optionValue) => {
    setSelectedAnswers((prev) => ({
      ...prev,
      [index]: optionValue,
    }));
  };

  const handleSubmitQuiz = async () => {
    setError(null);
    if (Object.keys(selectedAnswers).length !== quizQuestions.length) {
      setError("Please answer all questions before submitting.");
      return;
    }

    const payload = { quiz: quizQuestions, answers: selectedAnswers };

    try {
      const token = await getAccessToken();
      const res = await axios.post(
        `http://localhost:8000/api/chats/${chatId}/submit-quiz/`,
        payload,
        { headers: { Authorization: `Bearer ${token}` } }
      );

      // 1) setăm link-ul de download
      setSavedQuizPath(res.data.saved_path);

      // 2) extragem review-ul și-l adăugăm în chat
      const review = res.data.review;
      setMessages((prev) => [
        ...prev,
        { role: review.role, content: review.content },
      ]);
    } catch (e) {
      console.error("Error submitting quiz:", e.response || e.message);
      setError("Eroare la trimiterea răspunsurilor.");
    }
  };

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
      const tipMsg = res.data;
      setMessages((prev) => [
        ...prev,
        { role: tipMsg.role, content: tipMsg.content },
      ]);
    } catch (e) {
      console.error("Error fetching tips:", e.response || e.message);
      setError("Eroare la generarea sfaturilor.");
    }
  };

  // ─── Overall Improvement Assistant ───────────
  const handleSummary = async () => {
    setError(null);
    try {
      const token = await getAccessToken();
      const res = await axios.post(
        `http://localhost:8000/api/chats/${chatId}/quiz-summary/`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      // res.data este ChatMessage-ul creat
      setMessages((m) => [
        ...m,
        { role: res.data.role, content: res.data.content },
      ]);
    } catch (e) {
      console.error("Error fetching summary:", e);
      setError("Eroare la generarea raportului de performanță.");
    }
  };

  return (
    <>
      <Header />
      <div className="app-container page-container chat-page-container">
        <h2 className="chat-title">Chat Room</h2>

        {/* ─── Chat message pane ───────────── */}
        <div className="message-pane">
          {messages.map((m, i) => (
            <div
              key={i}
              className={`message-item ${m.role === "user" ? "user" : "assistant"}`}
            >
              <div className={`message-bubble ${m.role}`}>
                {m.content}
              </div>
            </div>
          ))}
          {isTyping && (
            <div className="message-item assistant">
              <div className="message-bubble assistant typing">
                …typing
              </div>
            </div>
          )}
        </div>

        {error && <p className="error-message">{error}</p>}

        {/* ─── Send new chat message ───────────── */}
        <form onSubmit={sendMessage} className="send-form">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type a message…"
            className="send-input"
          />
          <button type="submit" className="btn-primary send-button">
            Send
          </button>
        </form>

        {/* ─── Upload Document ───────────── */}
        <UploadDocumentPage
          chatId={chatId}
          onSuccess={handleDocUploadSuccess}
        />

        {/* ── Improvement Assistant Button ── */}
        <div style={{ margin: "20px 0", textAlign: "center" }}>
          <button
            onClick={handleSummary}
            style={{
              backgroundColor: "#17a2b8",
              color: "#fff",
              padding: "8px 16px",
              border: "none",
              borderRadius: 4,
              cursor: "pointer"
            }}
          >
            Asistent îmbunătățire
          </button>
        </div>

        {/* ─── Quiz generation UI ───────────── */}
        <div className="quiz-generation">
          <h3>Generează un Quiz</h3>
          <form onSubmit={handleGenerateQuiz} className="quiz-form">
            <div className="quiz-input-group">
              <label>Număr întrebări:</label>
              <input
                type="number"
                min="1"
                max="20"
                value={numQuestions}
                onChange={(e) => setNumQuestions(e.target.value)}
              />
            </div>
            <div className="quiz-input-group">
              <label>Dificultate:</label>
              <select
                value={difficulty}
                onChange={(e) => setDifficulty(e.target.value)}
              >
                <option value="easy">Ușor</option>
                <option value="medium">Mediu</option>
                <option value="hard">Greu</option>
              </select>
            </div>
            <div className="quiz-input-group">
              <label>Tip întrebare:</label>
              <select
                value={questionType}
                onChange={(e) => setQuestionType(e.target.value)}
              >
                <option value="multiple">Multiple Choice</option>
                <option value="truefalse">True/False</option>
              </select>
            </div>
            <button type="submit" className="btn-primary">
              Generează
            </button>
          </form>
        </div>

        {quizQuestions.length > 0 && (
          <div className="quiz-questions-container">
            <h4>Întrebările Quiz-ului:</h4>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSubmitQuiz();
              }}
              className="quiz-questions-form"
            >
              <ol>
                {quizQuestions.map((q, index) => (
                  <li key={index} className="quiz-question-item">
                    <p className="quiz-question-text">{q.question}</p>
                    <div className="quiz-options">
                      {q.options.map((opt, i) => (
                        <label key={i} className="quiz-option-label">
                          <input
                            type="radio"
                            name={`question_${index}`}
                            value={opt}
                            checked={selectedAnswers[index] === opt}
                            onChange={() => handleOptionChange(index, opt)}
                          />
                          <span className="option-text">
                            {opt === "true" ? "True" : opt === "false" ? "False" : opt}
                          </span>
                        </label>
                      ))}
                    </div>
                  </li>
                ))}
              </ol>
              <button type="submit" className="btn-success">
                Confirmă răspunsurile
              </button>
            </form>

            {savedQuizPath && (
              <div className="quiz-actions">
                <p>Răspunsurile au fost salvate!</p>
                <p>
                  Dacă vrei să primești sfaturi detaliate despre răspunsurile tale,
                  apasă pe butonul de mai jos. Pentru a putea avea o discuție pe baza
                  acestora, folosește chat-ul din partea de sus a paginii. Spune-i ce ai nevoie!
                </p>
                <button onClick={handleGetTips} className="btn-warning">
                  Sfaturi și trucuri
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </>
  );
}
