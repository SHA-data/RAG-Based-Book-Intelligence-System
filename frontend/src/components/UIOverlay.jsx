import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useScroll } from '@react-three/drei';
import { Upload, Search, BookOpen, Send, Library, Trash2 } from 'lucide-react';

const API_BASE = 'http://localhost:8000';

// Safely extracts a clean, single-line error message for the UI
const getCleanErrorMessage = (errData) => {
  if (!errData) return 'An unexpected error occurred.';
  const detail = errData.detail;
  if (typeof detail === 'string') {
    // Take only the first line of any long stack trace/error dump
    const firstLine = detail.split('\n')[0];
    return firstLine.length > 120 ? firstLine.substring(0, 120) + '...' : firstLine;
  }
  if (Array.isArray(detail)) {
    // Format validation errors cleanly (e.g. "body.question: field required")
    const firstErr = detail[0];
    if (firstErr) {
      return `${firstErr.loc?.join('.') || 'input'}: ${firstErr.msg}`;
    }
  }
  if (typeof detail === 'object' && detail !== null) {
    return JSON.stringify(detail);
  }
  return String(detail || 'Request failed.');
};

function Typewriter({ text, delay = 100 }) {
  const [currentText, setCurrentText] = useState('');
  const [currentIndex, setCurrentIndex] = useState(0);

  useEffect(() => {
    if (currentIndex < text.length) {
      const timeout = setTimeout(() => {
        setCurrentText((prev) => prev + text[currentIndex]);
        setCurrentIndex((prev) => prev + 1);
      }, delay);
      return () => clearTimeout(timeout);
    }
  }, [currentIndex, delay, text]);

  return <span className="typewriter-cursor">{currentText}</span>;
}

export default function UIOverlay() {
  const scroll = useScroll();
  const [query, setQuery] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [books, setBooks] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState('');

  // Fetch books from the database
  const fetchBooks = async () => {
    try {
      const res = await fetch(`${API_BASE}/books`);
      if (res.ok) {
        const data = await res.json();
        setBooks(data.books);
      }
    } catch (err) {
      console.error('Error fetching books:', err);
    }
  };

  useEffect(() => {
    fetchBooks();
  }, []);

  const handleQuery = async (e) => {
    e.preventDefault();
    if (!query) return;
    setLoading(true);
    setResult(null);
    try {
      const res = await fetch(`${API_BASE}/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: query,
          book_ids: null, // query across all books
        }),
      });

      if (res.ok) {
        const data = await res.json();
        setResult(data);
      } else {
        // Handle JSON error payload cleanly
        const errData = await res.json().catch(() => ({ detail: 'Server error occurred.' }));
        setResult({
          error: getCleanErrorMessage(errData),
        });
      }
    } catch (err) {
      setResult({
        error: 'Connection failed. Please ensure the backend server is running.',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setUploadStatus('Uploading and indexing book...');

    const formData = new FormData();
    formData.append('file', file);
    formData.append('book_title', file.name.split('.')[0]);

    try {
      const res = await fetch(`${API_BASE}/upload`, {
        method: 'POST',
        body: formData,
      });

      if (res.ok) {
        const data = await res.json();
        setUploadStatus(`Success! Ingested: ${data.book_title}`);
        fetchBooks();
      } else {
        const errData = await res.json().catch(() => ({ detail: 'Failed to upload file.' }));
        setUploadStatus(`Upload failed: ${getCleanErrorMessage(errData)}`);
      }
    } catch (err) {
      setUploadStatus('Connection error during upload.');
    } finally {
      setUploading(false);
    }
  };


  const handleDeleteBook = async (title) => {
    if (!confirm(`Are you sure you want to delete "${title}"?`)) return;

    try {
      const res = await fetch(`${API_BASE}/books/${encodeURIComponent(title)}`, {
        method: 'DELETE',
      });
      if (res.ok) {
        fetchBooks();
      }
    } catch (err) {
      console.error('Error deleting book:', err);
    }
  };

  return (
    <div className="ui-container">
      {/* Page 1: Hero */}
      <section className="section hero-section">
        <motion.div 
          className="hero-content"
          initial={{ opacity: 0, y: 50 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
        >
          <h1 className="interactive-title">
            <Typewriter text="RAG Knowledge Base" delay={80} />
          </h1>

          <p>Turn your books into a searchable AI oracle. Upload PDFs, EPUBs, or TXTs and get intelligent, cited answers instantly.</p>
          <div className="input-group" style={{ marginTop: '2rem' }}>
            <button 
              className="btn-primary" 
              onClick={() => {
                if (scroll?.el) {
                  scroll.el.scrollTo({ top: scroll.el.clientHeight, behavior: 'smooth' });
                }
              }}
            >
              <Upload size={20} /> Upload a Book
            </button>
            <button 
              className="btn-secondary" 
              onClick={() => {
                if (scroll?.el) {
                  scroll.el.scrollTo({ top: scroll.el.clientHeight * 2, behavior: 'smooth' });
                }
              }}
            >
              <Search size={20} /> Query Library
            </button>
          </div>
        </motion.div>
      </section>


      {/* Page 2: Upload */}
      <section className="section section-right">
        <motion.div 
          className="glass-card"
          initial={{ opacity: 0, x: 50 }}
          whileInView={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.8 }}
        >
          <h2 className="interactive-title"><Upload className="icon-large" /> Ingest Knowledge</h2>
          <p>Drop your documents here to embed them into the vector database.</p>
          
          <label className="file-drop-zone" style={{ display: 'block' }}>
            <Upload size={40} style={{ color: 'var(--text-muted)', marginBottom: '1rem' }} />
            <p>{uploading ? 'Processing...' : 'Click to upload files'}</p>
            <input 
              type="file" 
              accept=".pdf,.txt,.epub" 
              onChange={handleFileUpload} 
              style={{ display: 'none' }} 
              disabled={uploading}
            />
            <p style={{ fontSize: '0.8rem', marginTop: '0.5rem' }}>Supports: .pdf, .txt, .epub</p>
          </label>
          {uploadStatus && (
            <p style={{ marginTop: '1rem', fontSize: '0.9rem', color: uploadStatus.startsWith('Success') ? '#34d399' : '#f87171' }}>
              {uploadStatus}
            </p>
          )}
        </motion.div>
      </section>

      {/* Page 3: Query */}
      <section className="section hero-section">
        <motion.div 
          className="glass-card"
          initial={{ opacity: 0, x: -50 }}
          whileInView={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.8 }}
          style={{ maxWidth: '600px' }}
        >
          <h2 className="interactive-title"><Search className="icon-large" /> Ask the Oracle</h2>
          <p>Ask plain language questions across all your uploaded books.</p>
          
          <form onSubmit={handleQuery} className="input-group">
            <input 
              type="text" 
              className="input-field" 
              placeholder="What does the author say about..." 
              value={query}
              onChange={e => setQuery(e.target.value)}
            />
            <button type="submit" className="btn-primary" disabled={loading}>
              {loading ? 'Thinking...' : <Send size={20} />}
            </button>
          </form>

          {result && (
            <motion.div 
              className="result-card"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
            >
              {result.error ? (
                <p style={{ color: '#f87171' }}>{result.error}</p>
              ) : (
                <div className="result-scroll-area">
                  <p style={{ color: 'var(--text-main)', fontSize: '1.05rem', lineHeight: '1.5' }}>{result.answer}</p>
                  
                  {result.sources && result.sources.length > 0 && (
                    <div style={{ marginTop: '1.2rem' }}>
                      <strong style={{ color: 'var(--accent)', fontSize: '0.85rem' }}>SOURCES:</strong>
                      {result.sources.map((src, i) => (
                        <div key={i} className="source-item">
                          <BookOpen size={14} style={{ display: 'inline', marginRight: '0.5rem', color: '#00f2fe' }} />
                          {src.book_title} — {src.chapter || 'N/A'}, Page {src.page}
                          {src.excerpt && (
                            <p style={{ fontSize: '0.78rem', fontStyle: 'italic', marginTop: '0.25rem', color: 'var(--text-muted)' }}>
                              "{src.excerpt.substring(0, 120)}..."
                            </p>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </motion.div>
          )}

        </motion.div>
      </section>

      {/* Page 4: Library */}
      <section className="section section-center">
        <motion.div
          initial={{ opacity: 0, y: 50 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          style={{ width: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center' }}
        >
          <h2 className="interactive-title"><Library className="icon-large" style={{ margin: '0 auto 1rem auto' }} /> Your Indexed Library</h2>

          <p>Books currently embedded in your vector database.</p>
          
          <div className="library-grid">
            {books.length === 0 ? (
              <p style={{ gridColumn: '1 / -1', color: 'var(--text-muted)' }}>No books uploaded yet.</p>
            ) : (
              books.map((bookTitle) => (
                <div key={bookTitle} className="book-item">
                  <BookOpen size={32} className="book-icon" />
                  <span style={{ fontSize: '0.9rem', fontWeight: 600, wordBreak: 'break-all' }}>{bookTitle}</span>
                  <button 
                    onClick={() => handleDeleteBook(bookTitle)}
                    style={{ background: 'none', border: 'none', color: '#f87171', cursor: 'pointer', marginTop: '0.5rem' }}
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              ))
            )}
          </div>
        </motion.div>
      </section>
    </div>
  );
}
