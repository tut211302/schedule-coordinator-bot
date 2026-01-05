import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import GoogleCalendarConnectButton from './components/GoogleCalendarConnectButton';
import AuthCallback from './pages/AuthCallback';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<GoogleCalendarConnectButton />} />
        <Route path="/auth/google/callback" element={<AuthCallback />} />
      </Routes>
    </Router>
  );
}

export default App;
