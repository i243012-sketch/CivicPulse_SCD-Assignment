import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { HomePage } from './pages/HomePage';
import { ErrorBoundary } from './components/ErrorBoundary';
import { RuntimeConfigCheck } from './components/RuntimeConfigCheck';
import './App.css';

function App() {
  return (
    <ErrorBoundary>
      <RuntimeConfigCheck>
        <Router>
          <Routes>
            <Route path="/" element={<HomePage />} />
          </Routes>
        </Router>
      </RuntimeConfigCheck>
    </ErrorBoundary>
  );
}

export default App;
