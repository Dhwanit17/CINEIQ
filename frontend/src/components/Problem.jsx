import { useScrollReveal } from '../hooks/useScrollReveal.js';

export default function Problem() {
  const [quoteRef, quoteCls] = useScrollReveal();
  const [svgRef, svgCls] = useScrollReveal();

  return (
    <section className="problem" id="problem">
      <div className="container">
        <div className="section-tag">§ 01 · The Problem</div>

        <blockquote ref={quoteRef} className={`pullquote ${quoteCls}`}>
          <span className="quote-mark">"</span>
          Content discovery on modern streaming platforms is{' '}
          <span className="hl-red">opaque</span>, biased toward{' '}
          <span className="hl-amber">promoted titles</span>, and traps users in{' '}
          <span className="hl-green">recommendation loops</span> they never agreed to.
        </blockquote>

        <div className="loop-viz">
          <div className="loop-viz-text">
            <h3>// The Loop Trap</h3>
            <p>
              You watch one action film. The algorithm shows you five more. You watch one. Now there
              are <strong>twenty</strong>. The feedback loop forgets you ever liked Tarkovsky.
            </p>
            <p>
              CINEIQ breaks the cycle with explainable, diversity-aware re-ranking — every
              recommendation comes with a{' '}
              <strong style={{ color: 'var(--phosphor)' }}>human-readable reason</strong> and a path
              back out.
            </p>
          </div>
          <div ref={svgRef} className={`loop-svg-wrap ${svgCls}`}>
            <svg
              viewBox="0 0 400 400"
              xmlns="http://www.w3.org/2000/svg"
              style={{ width: '100%', height: '100%' }}
            >
              <defs>
                <filter id="glow">
                  <feGaussianBlur stdDeviation="3" result="b" />
                  <feMerge>
                    <feMergeNode in="b" />
                    <feMergeNode in="SourceGraphic" />
                  </feMerge>
                </filter>
              </defs>

              {/* Loop circle */}
              <circle
                cx="200"
                cy="200"
                r="120"
                fill="none"
                stroke="#ff3b3b"
                strokeWidth="1"
                strokeDasharray="4 4"
                opacity="0.6"
              >
                <animateTransform
                  attributeName="transform"
                  type="rotate"
                  from="0 200 200"
                  to="360 200 200"
                  dur="20s"
                  repeatCount="indefinite"
                />
              </circle>

              {/* Loop nodes */}
              <g filter="url(#glow)">
                <circle cx="320" cy="200" r="8" fill="#ff3b3b">
                  <animate attributeName="r" values="6;10;6" dur="2s" repeatCount="indefinite" />
                </circle>
                <circle cx="260" cy="304" r="6" fill="#ff3b3b" opacity="0.8">
                  <animate
                    attributeName="r"
                    values="5;8;5"
                    dur="2s"
                    begin="0.4s"
                    repeatCount="indefinite"
                  />
                </circle>
                <circle cx="140" cy="304" r="6" fill="#ff3b3b" opacity="0.7">
                  <animate
                    attributeName="r"
                    values="5;8;5"
                    dur="2s"
                    begin="0.8s"
                    repeatCount="indefinite"
                  />
                </circle>
                <circle cx="80" cy="200" r="6" fill="#ff3b3b" opacity="0.6">
                  <animate
                    attributeName="r"
                    values="5;8;5"
                    dur="2s"
                    begin="1.2s"
                    repeatCount="indefinite"
                  />
                </circle>
                <circle cx="140" cy="96" r="6" fill="#ff3b3b" opacity="0.5">
                  <animate
                    attributeName="r"
                    values="5;8;5"
                    dur="2s"
                    begin="1.6s"
                    repeatCount="indefinite"
                  />
                </circle>
                <circle cx="260" cy="96" r="6" fill="#ff3b3b" opacity="0.6">
                  <animate
                    attributeName="r"
                    values="5;8;5"
                    dur="2s"
                    begin="2s"
                    repeatCount="indefinite"
                  />
                </circle>
              </g>

              {/* Center user */}
              <circle cx="200" cy="200" r="14" fill="none" stroke="#8a8a82" strokeWidth="1" />
              <text
                x="200"
                y="205"
                textAnchor="middle"
                fontFamily="Share Tech Mono"
                fontSize="11"
                fill="#e8e8e2"
              >
                USR
              </text>

              {/* Escape arrow */}
              <g filter="url(#glow)">
                <line x1="200" y1="180" x2="200" y2="40" stroke="#00ff88" strokeWidth="2">
                  <animate
                    attributeName="stroke-dasharray"
                    values="0 200;200 0"
                    dur="3s"
                    repeatCount="indefinite"
                  />
                </line>
                <polygon points="200,30 192,50 208,50" fill="#00ff88" />
                <text
                  x="215"
                  y="100"
                  fontFamily="Share Tech Mono"
                  fontSize="12"
                  fill="#00ff88"
                  letterSpacing="2"
                >
                  ESCAPE
                </text>
              </g>

              {/* New space nodes */}
              <circle cx="200" cy="20" r="5" fill="#00ff88" filter="url(#glow)">
                <animate attributeName="opacity" values="0;1" dur="3s" repeatCount="indefinite" />
              </circle>
              <circle cx="60" cy="40" r="4" fill="#ffaa00" filter="url(#glow)" opacity="0.5" />
              <circle cx="350" cy="60" r="4" fill="#ffaa00" filter="url(#glow)" opacity="0.5" />
              <circle cx="40" cy="120" r="3" fill="#00ff88" filter="url(#glow)" opacity="0.4" />
              <circle cx="360" cy="140" r="3" fill="#00ff88" filter="url(#glow)" opacity="0.4" />

              {/* Frame label */}
              <text
                x="20"
                y="380"
                fontFamily="Share Tech Mono"
                fontSize="9"
                fill="#4a4a44"
                letterSpacing="2"
              >
                fig. 01 — recommendation loop & escape vector
              </text>
            </svg>
          </div>
        </div>
      </div>
    </section>
  );
}
