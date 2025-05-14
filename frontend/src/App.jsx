import React, { useState } from 'react';
import UploadForm from './components/UploadForm';
import ResponseView from './components/ResponseViewer';
import YouTubeSelector from './components/YouTubeSelector';
import LiveVideo from './components/LiveVideo';
import QuestionForm from './components/QuestionForm';
import './App.css';

function App() {
  const [response, setResponse] = useState('');

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="app-header-content">
          <a href="/" className="app-logo">EchoFrame</a>
          <nav>
            <button className="button button-secondary">Documentation</button>
          </nav>
        </div>
      </header>

      <main className="app-main">

        <div className="card">
          <div className="section-title">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
              <path d="M10.5 3a1.5 1.5 0 00-1.5 1.5v15a1.5 1.5 0 003 0v-15A1.5 1.5 0 0010.5 3zM4.5 3a1.5 1.5 0 00-1.5 1.5v15a1.5 1.5 0 003 0v-15A1.5 1.5 0 004.5 3zM16.5 3a1.5 1.5 0 00-1.5 1.5v15a1.5 1.5 0 003 0v-15A1.5 1.5 0 0016.5 3z" />
            </svg>
            <h2>Select YouTube Videos</h2>
          </div>
          <YouTubeSelector onVideosSelected={(videoList) => {
            console.log('Selected videos:', videoList)
          }
          }
          />
        </div>

        <div className="card">
          <QuestionForm />

        </div>

        <div className="card">
          <div className="section-title">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
              <path d="M5.625 1.5c-1.036 0-1.875.84-1.875 1.875v17.25c0 1.035.84 1.875 1.875 1.875h12.75c1.035 0 1.875-.84 1.875-1.875V12.75A3.75 3.75 0 0016.5 9h-1.875a1.875 1.875 0 01-1.875-1.875V5.25A3.75 3.75 0 009 1.5H5.625z" />
            </svg>
            <h2>Podcast</h2>
          </div>
          <ResponseView response={response} />
        </div>
        <div className="card">
          <div className="section-title">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
              <path d="M4.5 3A1.5 1.5 0 003 4.5v15A1.5 1.5 0 004.5 21h15a1.5 1.5 0 001.5-1.5v-15A1.5 1.5 0 0019.5 3h-15z" />
            </svg>
            <h2>Live Video Conversation</h2>
          </div>
          <LiveVideo />
        </div>
      </main>
    </div>
  );
}

export default App;