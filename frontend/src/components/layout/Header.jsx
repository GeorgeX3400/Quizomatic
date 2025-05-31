import React from 'react';
import { Link } from 'react-router-dom'; // ai folosit react-router-dom pentru celelalte rute
import './Header.css';

const Header = () => {
  return (
    <header className="app-header">
      <h1>Quizomatic</h1>
      <nav>
        <Link to="/">Home</Link>
        <Link to="/about">Abouts us</Link> {/* Dacă nu ai pagina /about, îl poți elimina */}
        <Link to="/contact">Contact</Link> {/* La fel, ștergi dacă nu există */}
      </nav>
    </header>
  );
};

export default Header;
