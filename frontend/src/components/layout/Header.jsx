import React from 'react';
import { Link } from 'react-router';

const Header = () => {
    return (
        <header style={{
            backgroundColor: '#3A59D1',
            color: '#FFFFFF',
            padding: '10px 20px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
            width: '98vw', /* Make the header span the entire width of the browser tab */
            position: 'fixed', /* Keep the header fixed at the top */
            top: 0, /* Align it to the top of the viewport */
            left: 0, /* Align it to the left of the viewport */
            zIndex: 1000 /* Ensure it stays above other elements */
        }}>
            <h1 style={{ margin: 0, fontSize: '1.5em' }}>Quizomatic</h1>
            <nav>
                <Link to="/" style={{ color: '#FFFFFF', textDecoration: 'none', margin: '0 10px' }}>Home</Link>
                <Link to="/about" style={{ color: '#FFFFFF', textDecoration: 'none', margin: '0 10px' }}>About</Link>
                <Link to="/contact" style={{ color: '#FFFFFF', textDecoration: 'none', margin: '0 10px' }}>Contact</Link>
            </nav>
        </header>
    );
};

export default Header;