import { useEffect, useRef, useState } from 'react';
import { demoData, demoMovieTitles } from '../data/demoData.js';
import { useScrollReveal } from '../hooks/useScrollReveal.js';

// Where the CINEIQ backend is running. Override at build time by setting
// VITE_CINEIQ_API_URL before `npm run build`.
const API_BASE = import.meta.env.VITE_CINEIQ_API_URL || 'http://localhost:8000';
const DEFAULT_MOVIE = 'Blade Runner 2049';

function pad2(n) {
  return String(n).padStart(2, '0');
}

function useClock() {
  const [time, setTime] = useState(() => {
    const d = new Date();
    return `${pad2(d.getHours())}:${pad2(d.getMinutes())}:${pad2(d.getSeconds())}`;
  });

  useEffect(() => {
    const id = setInterval(() => {
      const d = new Date();
      setTime(`${pad2(d.getHours())}:${pad2(d.getMinutes())}:${pad2(d.getSeconds())}`);
    }, 1000);
    return () => clearInterval(id);
  }, []);

  return time;
}

/** Convert the API response into the shape the UI already knew. */
function adaptApiResponse(payload) {
  return {
    meta: {
      genre: payload.meta.genres || '—',
      mood: payload.meta.model,
      runtime: `${payload.meta.latency_ms}ms`,
    },
    recs: payload.results.map((r) => ({
      title: r.title,
      year: r.year,
      score: r.score_pct,
      reason: r.reason,
      // The two bars: CF (or content if CF wasn't a signal), and sentiment.
      cf: Math.round(
        ((r.signals.collaborative ?? r.signals.content ?? 0.5) * 100)
      ),
      sent: Math.round(((r.signals.sentiment ?? 0) + 1) / 2 * 100),
    })),
  };
}

function localFallback(title) {
  return demoData[title] ?? null;
}

function Recommendation({ rec, index }) {
  return (
    <div className="rec" style={{ animation: `fadeUp 0.4s ease ${index * 0.06}s both` }}>
      <div className="rec-score">
        {rec.score}
        <sub>%</sub>
      </div>
      <div className="rec-info">
        <div>
          <span className="title">{rec.title}</span>
          <span className="year">· {rec.year}</span>
        </div>
        <div
          className="reason"
          dangerouslySetInnerHTML={{ __html: `→ ${rec.reason}` }}
        />
      </div>
      <div className="rec-bars">
        <div className="rec-bar">
          <span className="label">CF</span>
          <div className="track">
            <div className="fill" style={{ width: `${rec.cf}%` }} />
          </div>
        </div>
        <div className="rec-bar">
          <span className="label">SNT</span>
          <div className="track">
            <div className="fill amber" style={{ width: `${rec.sent}%` }} />
          </div>
        </div>
      </div>
    </div>
  );
}

export default function Demo() {
  const time = useClock();
  const [terminalRef, terminalCls] = useScrollReveal();

  const [inputValue, setInputValue] = useState(DEFAULT_MOVIE);
  const [selectedTitle, setSelectedTitle] = useState(DEFAULT_MOVIE);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  // Banner showing whether we're hitting the live API or local cache
  const [source, setSource] = useState('cache');

  const inputRef = useRef(null);

  // Fetch whenever the selected title changes
  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    (async () => {
      try {
        const url = `${API_BASE}/recommend?title=${encodeURIComponent(selectedTitle)}&top_n=8`;
        const resp = await fetch(url, { signal: AbortSignal.timeout(5000) });
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const json = await resp.json();
        if (cancelled) return;
        setData(adaptApiResponse(json));
        setSource('live');
      } catch (e) {
        if (cancelled) return;
        const cached = localFallback(selectedTitle);
        if (cached) {
          setData(cached);
          setSource('cache');
        } else {
          setError(
            `// NO_INDEX_HIT · "${selectedTitle}" not in API or demo cache · pick a chip below ↓`
          );
          setData(null);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [selectedTitle]);

  const selectMovie = (title) => {
    setInputValue(title);
    setSelectedTitle(title);
  };

  const onKeyDown = (e) => {
    if (e.key !== 'Enter') return;
    const v = inputValue.trim();
    if (v) setSelectedTitle(v);
  };

  return (
    <section className="demo" id="demo">
      <div className="container">
        <div className="section-tag">§ 03 · Live Demo</div>
        <h2 className="section-title">
          Type a film. <em>Get answers.</em>
        </h2>

        <div ref={terminalRef} className={`terminal ${terminalCls}`}>
          <div className="terminal-bar">
            <div className="terminal-dots">
              <span />
              <span />
              <span />
            </div>
            <div className="terminal-title">cineiq@kernel ~ /recommend --explain</div>
            <div className="terminal-time">{time}</div>
          </div>
          <div className="terminal-body">
            <div className="prompt-line">
              <span className="arrow">▸</span>
              <input
                ref={inputRef}
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={onKeyDown}
                autoComplete="off"
                spellCheck="false"
              />
              <span className="cursor" />
            </div>

            <div className="quick-chips">
              {demoMovieTitles.map((title) => (
                <button
                  key={title}
                  className={`chip${selectedTitle === title ? ' active' : ''}`}
                  onClick={() => selectMovie(title)}
                >
                  {title}
                </button>
              ))}
            </div>

            <div className="demo-output">
              {error && (
                <div className="demo-meta" style={{ color: 'var(--amber)' }}>
                  {error}
                </div>
              )}
              {loading && !data && (
                <div className="demo-meta">
                  <span className="key">→</span> querying{' '}
                  <span className="val">{API_BASE}</span>...
                </div>
              )}
              {data && (
                <>
                  <div className="demo-meta">
                    <span className="key">QUERY</span> = "
                    <span className="val">{selectedTitle}</span>"
                    &nbsp;·&nbsp; <span className="key">GENRE</span> ={' '}
                    <span className="val">{data.meta.genre}</span>
                    &nbsp;·&nbsp; <span className="key">MOOD</span> ={' '}
                    <span className="val">{data.meta.mood}</span>
                    &nbsp;·&nbsp; <span className="key">RT</span> ={' '}
                    <span className="val">{data.meta.runtime}</span>
                    &nbsp;·&nbsp; <span className="key">SOURCE</span> ={' '}
                    <span
                      className="val"
                      style={{
                        color: source === 'live' ? 'var(--phosphor)' : 'var(--amber)',
                      }}
                    >
                      {source === 'live' ? 'LIVE_API' : 'LOCAL_CACHE'}
                    </span>
                  </div>
                  <div className="demo-meta">
                    <span className="key">→</span> returning{' '}
                    <span className="val">{data.recs.length}</span> recommendations ·{' '}
                    <span className="key">model</span> ={' '}
                    <span className="val">hybrid + sentiment</span>
                  </div>
                  <div className="recs">
                    {data.recs.map((rec, i) => (
                      <Recommendation
                        key={`${selectedTitle}-${rec.title}-${i}`}
                        rec={rec}
                        index={i}
                      />
                    ))}
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
