import { useState } from 'react'
import './App.css'

type Source = {
  title: string
  page: number | string | null
  snippet: string
}

type Message = {
  question: string
  answer: string
  sources: Source[]
}

function App() {
  const [question, setQuestion] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const [showSources, setShowSources] = useState(false)
  const [activeSources, setActiveSources] = useState<Source[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function sendMessage(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()

    const text = question.trim()
    if (!text || loading) return

    setLoading(true)
    setError('')
    setQuestion('')

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: text }),
      })

      if (!response.ok) {
        throw new Error(`Request failed (${response.status})`)
      }

      const data = await response.json()

      const sources: Source[] = (data.sources ?? []).map(
        (source: {
          title?: string
          filename?: string
          page: number | string | null
          snippet: string
        }) => ({
          title: source.title ?? source.filename ?? 'Unknown document',
          page: source.page,
          snippet: source.snippet,
        }),
      )

      setMessages((previous) => [
        ...previous,
        { question: text, answer: data.answer, sources },
      ])
      setActiveSources(sources)
    } catch {
      setError('Could not get a response. Check that the backend is running.')
      setQuestion(text)
    } finally {
      setLoading(false)
    }
  }

  function newChat() {
    setMessages([])
    setQuestion('')
    setError('')
    setShowSources(false)
    setActiveSources([])
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand-container">
          <span className="brand-name">CRAGbot</span>
          <span className="brand-subtitle">Coral Reef Advisory Group Library Assistant</span>
        </div>

        <button className="new-chat" onClick={newChat} title="New chat">
          <svg
            width="15"
            height="15"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M12 20h9" />
            <path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L8 18l-4 1 1-4Z" />
          </svg>
          New chat
        </button>
      </header>

      <div className="workspace">
        <main className="chat-main">
          <div className="chat-content">
            {messages.length === 0 && (
              <section className="welcome">
                <h1>What would you like to explore?</h1>
              </section>
            )}

            <section className="messages">
              {messages.map((message, index) => (
                <div className="conversation" key={index}>
                  <div className="message user-message">
                    <div className="bubble user-bubble">
                      {message.question}
                    </div>
                  </div>

                  <div className="assistant-message">
                    <div className="assistant-body">
                      <div className="bubble assistant-bubble">
                        <p>{message.answer}</p>

                        {message.sources.length > 0 && (
                          <button
                            className="sources-button"
                            onClick={() => {
                              setActiveSources(message.sources)
                              setShowSources(true)
                            }}
                          >
                            {message.sources.length} sources
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}

              {loading && (
                <div className="loading">Thinking...</div>
              )}
            </section>

            {error && <p className="error">{error}</p>}

            <form className="composer" onSubmit={sendMessage}>
              <textarea
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault()
                    e.currentTarget.form?.requestSubmit()
                  }
                }}
                placeholder="Ask a question..."
                rows={1}
                disabled={loading}
              />
              <button
                className="send-button"
                type="submit"
                disabled={loading || !question.trim()}
                aria-label="Send message"
              >
                ↑
              </button>
            </form>
          </div>
        </main>

        {showSources && (
          <aside className="sources-sidebar">
            <div className="sources-header">
              <h2>Sources</h2>
              <button
                className="close-button"
                onClick={() => setShowSources(false)}
                aria-label="Close sources"
              >
                ×
              </button>
            </div>

            <div className="source-list">
              {activeSources.map((source, index) => (
                <article className="source-card" key={`${source.title}-${index}`}>
                  <h3>{source.title}</h3>
                  <p>{source.snippet}</p>
                </article>
              ))}
            </div>
          </aside>
        )}
      </div>
    </div>
  )
}

export default App
