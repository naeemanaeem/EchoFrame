import React, { useState, useEffect, useRef } from 'react';

export default function ResponseViewer() {
  const [language, setLanguage] = useState('en');
  const [englishText, setEnglishText] = useState('');
  const [translatedText, setTranslatedText] = useState('');
  const [loadingAudio, setLoadingAudio] = useState(false);
  const [error, setError] = useState('');
  const audioRef = useRef(null);
  const [audioUrl, setAudioUrl] = useState(null);

  // Fetch English podcast text on mount
  useEffect(() => {
    const fetchEnglishText = async () => {
      try {
        const res = await fetch('http://localhost:8000/podcast-text?lang=en');
        if (!res.ok) throw new Error('Failed to fetch English podcast text');
        const text = await res.text();
        setEnglishText(text);
      } catch (err) {
        console.error(err);
        setEnglishText('Error loading English content.');
      }
    };
    fetchEnglishText();
  }, []);

  const handleLanguageChange = async (e) => {
    const selectedLang = e.target.value;
    setLanguage(selectedLang);

    if (selectedLang === 'en') {
      setTranslatedText('');
      return;
    }

    try {
      const res = await fetch('http://localhost:8000/test-translations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ language: selectedLang }),
      });

      if (!res.ok) throw new Error('Failed to fetch translation');
      const text = await res.text();
      setTranslatedText(text);
    } catch (err) {
      console.error(err);
      setTranslatedText('Error loading translated content.');
    }
  };

  const handlePlayClick = async () => {
    setLoadingAudio(true);
    setError('');
    try {
      const res = await fetch('http://localhost:8000/generate-speech', { method: 'POST' });
      
      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.error || 'Failed to generate speech');
      }

      const contentType = res.headers.get('content-type');
      if (!contentType || !contentType.includes('audio/wav')) {
        throw new Error('Invalid response format');
      }

      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      setAudioUrl(url);
    } catch (error) {
      console.error('Error generating speech:', error);
      setError(error.message || 'Failed to generate speech. Please try again.');
      setAudioUrl(null);
    } finally {
      setLoadingAudio(false);
    }
  };

  return (
    <div className="response-viewer">
      <div className="response-header">
        <label htmlFor="language-select">Language: </label>
        <select
          id="language-select"
          value={language}
          onChange={handleLanguageChange}
          className="language-dropdown"
        >
          <option value="en">English</option>
          <option value="es">Spanish</option>
          <option value="fr">French</option>
          <option value="hi">Hindi</option>
          <option value="zh">Chinese</option>
        </select>

        <button 
          onClick={handlePlayClick} 
          disabled={loadingAudio} 
          className={`play-button ${loadingAudio ? 'loading' : ''}`}
        >
          {loadingAudio ? 'Generating Audio...' : 'Play'}
        </button>

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        {audioUrl && (
          <audio ref={audioRef} controls src={audioUrl} className="audio-player" />
        )}
      </div>

      <div className="language-block">
        <pre className="response-content">{englishText}</pre>
      </div>

      {language !== 'en' && (
        <div className="language-block">
          <h4>Translated ({language})</h4>
          <pre className="response-content">{translatedText}</pre>
        </div>
      )}
    </div>
  );
}