// src/pages/AboutPage.jsx

import React from "react";
import Header from "../components/layout/Header";

const AboutPage = () => {
  return (
    <>
      <Header />

      <div className="app-container page-container">
        <h2>Despre noi</h2>

      <p>
        Quizomatic este o platformă modernă, construită pentru a transforma studiul pasiv în experiențe interactive care accelerează procesul de învățare și fixează noțiunile în profunzime. Echipa noastră își propune să ofere o soluție ingenioasă pentru oricine dorește să înțeleagă mai bine materialele de curs, articolele științifice sau orice document informațional, prin generarea automată de quiz-uri personalizate.
      </p>

      <h3>Ce probleme rezolvăm?</h3>
      <ul>
        <li>
          <strong>Înlocuim lectura pasivă cu antrenamentul activ al memoriei.</strong> În loc să parcurgi pagini lungi de text fără un feedback imediat, Quizomatic generează întrebări relevante direct din documentele încărcate, astfel încât fiecare parcurgere devine o verificare inteligentă a nivelului tău de cunoștințe.
        </li>
        <li>
          <strong>Adaptăm quiz-urile pe măsura progresului tău.</strong> Fie că ai nevoie de întrebări cu variante multiple sau de adevărat/fals, alegi tu dificultatea și numărul de întrebări. Quiz-urile pot fi concepute pentru a fi mai simple sau mai provocatoare, în funcție de nevoile tale de învățare.
        </li>
      </ul>

      <h3>Cum funcționează Quizomatic?</h3>
      <ol>
        <li>
          <strong>Încărcarea documentului</strong> (PDF, DOCX, TXT): Selectezi fișierul din care vrei să înveți.
        </li>
        <li>
          <strong>Configurarea quiz-ului</strong>: Alegi câte întrebări vrei, nivelul de dificultate (ușor, mediu, dificil) și tipul acestora (multiple choice sau adevărat/fals).
        </li>
        <li>
          <strong>Generarea automată</strong>: În câteva secunde, motorul nostru de inteligență artificială analizează conținutul și creează un set de întrebări relevante.
        </li>
        <li>
          <strong>Rezolvare și feedback</strong>: Parcurgi quiz-ul, primești imediat răspunsurile corecte, iar dacă greșești, poți cere explicații detaliate pentru fiecare întrebare.
        </li>
      </ol>

      <p>
        Pe lângă quiz-uri, poți solicita și un <strong>rezumat automat al documentului</strong>: aplicația extrage conceptele-cheie și îți prezintă o sinteză a materialului, ideală pentru o recapitulare rapidă. În funcție de performanța ta la quiz-uri, poți primi <strong>feedback personalizat</strong> care te îndrumă spre zonele în care ai nevoie de îmbunătățiri.
      </p>

      <h3>Cine suntem noi?</h3>
      <p>
        Ne mândrim cu o echipă diversă, formată din studenți pasionați de tehnologie și educație:
      </p>
      <ul>
        <li><strong>Șerbănescu George</strong> – Student FMI, anul II, grupa 251</li>
        <li><strong>Mihăilă Denisa</strong> – Studentă FMI, anul II, grupa 252</li>
        <li><strong>Nițe Alexandru</strong> – Student FMI, anul II, grupa 244</li>
      </ul>

      <p>
        Suntem uniți de dorința de a face învățarea mai eficientă și mai plăcută. Am lucrat împreună la alegerea celor mai potrivite tehnologii (React, Django, LLM-uri) și la design-ul unui flux intuitiv, astfel încât utilizatorii să-și poată transforma materialele de referință în instrumente de studiu practice.
      </p>

      </div>
    </>
  );
};

export default AboutPage;
