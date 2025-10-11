import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css"; 
import App from "./App.jsx";
import ErrorBoundary from "./components/ErrorBoundary.jsx";
import { BrowserRouter as Router } from 'react-router-dom';

createRoot(document.getElementById("root")).render(
  <ErrorBoundary>
    <Router>
      <App />
    </Router>
  </ErrorBoundary>
);
