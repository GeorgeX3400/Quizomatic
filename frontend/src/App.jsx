// frontend/src/App.jsx

import React from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import MainPage from "./pages/MainPage";
import CreateChatPage from "./pages/CreateChatPage";
import ChatPage from "./pages/ChatPage";
import ContactPage from "./pages/ContactPage";
import AboutPage   from "./pages/AboutPage";


import "./App.css";

function App() {
  return (
    <Router>
      <div className="app-container">
        <Routes>
          <Route path="/dashboard" element={<MainPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/create-chat" element={<CreateChatPage />} />
          <Route path="/chats/:chatId" element={<ChatPage />} />
          <Route path="/about" element={<AboutPage />} />
          <Route path="/contact" element={<ContactPage />} />
          
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
