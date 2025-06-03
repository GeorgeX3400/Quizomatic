// src/pages/ContactPage.jsx

import React from "react";
import Header from "../components/layout/Header";

const ContactPage = () => {
  return (
    <>
      <Header />

      <div className="app-container page-container">
        <h2>Contact</h2>

      <p>
        Dacă ai nevoie de asistență, sugestii sau pur și simplu vrei să ne saluți, echipa Quizomatic îți stă la dispoziție. Trimite-ne un e-mail la oricare dintre adresele de mai jos și îți vom răspunde în cel mai scurt timp:
      </p>

      <ul>
        <li>
          <strong>Șerbănescu George</strong> – <a href="mailto:george-florin.serbanescu@s.unibuc.ro">george-florin.serbanescu@s.unibuc.ro</a>
        </li>
        <li>
          <strong>Mihăilă Denisa</strong> – <a href="mailto:denisa.mihaila@s.unibuc.ro">denisa.mihaila@s.unibuc.ro</a>
        </li>
        <li>
          <strong>Nițe Alexandru</strong> – <a href="mailto:dan-alexandru.nite@s.unibuc.ro">dan-alexandru.nite@s.unibuc.ro</a>
        </li>
      </ul>

      <p>
        Ne poți scrie oricând ai nevoie de informații suplimentare despre cum funcționează Quizomatic, despre integrarea cu documente de curs sau despre viitoarele funcționalități. Îți mulțumim că ai ales Quizomatic pentru a-ți îmbunătăți experiența de învățare!
      </p>
      </div>
    </>
  );
};

export default ContactPage;
