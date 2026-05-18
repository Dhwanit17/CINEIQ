import { useScrollReveal } from '../hooks/useScrollReveal.js';

// Architecture pipeline nodes, defined as data for clarity.
const NODES = [
  {
    x: 20,
    width: 150,
    titleX: 95,
    title: 'Raw Data',
    sub1: 'MovieLens · TMDB',
    sub2: 'IMDB',
    stroke: '#4a4a44',
    strokeWidth: 1,
    titleColor: '#e8e8e2',
  },
  {
    x: 230,
    width: 150,
    titleX: 305,
    title: 'Feature Eng.',
    sub1: 'TF-IDF · embed',
    sub2: 'normalize',
    stroke: '#4a4a44',
    strokeWidth: 1,
    titleColor: '#e8e8e2',
  },
  {
    x: 440,
    width: 150,
    titleX: 515,
    title: 'Hybrid Engine',
    sub1: 'CF + Content',
    sub2: '+ SVD',
    stroke: '#00ff88',
    strokeWidth: 1.5,
    titleColor: '#00ff88',
  },
  {
    x: 650,
    width: 150,
    titleX: 725,
    title: 'Sentiment Re-Rank',
    sub1: 'VADER · BERT',
    sub2: '+ diversity',
    stroke: '#ffaa00',
    strokeWidth: 1.5,
    titleColor: '#ffaa00',
  },
  {
    x: 860,
    width: 150,
    titleX: 935,
    title: 'Explainability',
    sub1: 'LIME + rules',
    sub2: '→ reasons',
    stroke: '#00ff88',
    strokeWidth: 1.5,
    titleColor: '#00ff88',
  },
  {
    x: 1070,
    width: 120,
    titleX: 1130,
    title: 'Dashboard',
    sub1: 'Streamlit',
    sub2: '+ Plotly',
    stroke: '#4a4a44',
    strokeWidth: 1,
    titleColor: '#e8e8e2',
  },
];

const FLOW_PATH =
  'M 170 180 L 220 180 L 220 180 L 380 180 L 380 180 L 430 180 L 430 180 L 590 180 L 590 180 L 640 180 L 640 180 L 800 180 L 800 180 L 850 180 L 850 180 L 1010 180 L 1010 180 L 1060 180';

export default function Architecture() {
  const [ref, cls] = useScrollReveal();

  return (
    <section className="arch" id="arch">
      <div className="container">
        <div className="section-tag">§ 06 · Architecture</div>
        <h2 className="section-title">
          <em>Data → Insight.</em>
        </h2>

        <div ref={ref} className={`arch-diagram ${cls}`}>
          <svg viewBox="0 0 1200 360" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <filter id="nodeglow">
                <feGaussianBlur stdDeviation="2" result="b" />
                <feMerge>
                  <feMergeNode in="b" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
              <marker
                id="arrow"
                viewBox="0 0 10 10"
                refX="9"
                refY="5"
                markerWidth="8"
                markerHeight="8"
                orient="auto"
              >
                <path d="M 0 0 L 10 5 L 0 10 z" fill="#00ff88" />
              </marker>
            </defs>

            {/* Connecting flow lines */}
            <g
              stroke="#00ff88"
              strokeWidth="1.5"
              fill="none"
              markerEnd="url(#arrow)"
              opacity="0.7"
            >
              <line x1="170" y1="180" x2="220" y2="180" />
              <line x1="380" y1="180" x2="430" y2="180" />
              <line x1="590" y1="180" x2="640" y2="180" />
              <line x1="800" y1="180" x2="850" y2="180" />
              <line x1="1010" y1="180" x2="1060" y2="180" />
            </g>

            {/* Data packet animations */}
            <circle r="3" fill="#ffaa00" filter="url(#nodeglow)">
              <animateMotion dur="6s" repeatCount="indefinite" path={FLOW_PATH} />
            </circle>
            <circle r="3" fill="#00ff88" filter="url(#nodeglow)">
              <animateMotion dur="6s" begin="2s" repeatCount="indefinite" path={FLOW_PATH} />
            </circle>

            {/* Nodes */}
            {NODES.map((n) => (
              <g key={n.title} className="arch-node">
                <rect
                  x={n.x}
                  y="130"
                  width={n.width}
                  height="100"
                  fill="rgba(15,15,16,0.8)"
                  stroke={n.stroke}
                  strokeWidth={n.strokeWidth}
                />
                <text
                  className="arch-label"
                  x={n.titleX}
                  y="170"
                  textAnchor="middle"
                  fontFamily="VT323"
                  fontSize="22"
                  fill={n.titleColor}
                >
                  {n.title}
                </text>
                <text
                  x={n.titleX}
                  y="192"
                  textAnchor="middle"
                  fontFamily="Share Tech Mono"
                  fontSize="9"
                  fill="#8a8a82"
                  letterSpacing="1"
                >
                  {n.sub1}
                </text>
                <text
                  x={n.titleX}
                  y="208"
                  textAnchor="middle"
                  fontFamily="Share Tech Mono"
                  fontSize="9"
                  fill="#8a8a82"
                  letterSpacing="1"
                >
                  {n.sub2}
                </text>
              </g>
            ))}

            {/* Top labels */}
            <text
              x="20"
              y="50"
              fontFamily="Share Tech Mono"
              fontSize="11"
              fill="#4a4a44"
              letterSpacing="2"
            >
              // PIPELINE_FLOW.SVG · v0.4.2
            </text>
            <line x1="20" y1="80" x2="1190" y2="80" stroke="#15161a" strokeWidth="1" />

            {/* Bottom labels */}
            <text x="20" y="320" fontFamily="Share Tech Mono" fontSize="10" fill="#4a4a44" letterSpacing="1">
              ingest
            </text>
            <text x="240" y="320" fontFamily="Share Tech Mono" fontSize="10" fill="#4a4a44" letterSpacing="1">
              transform
            </text>
            <text x="450" y="320" fontFamily="Share Tech Mono" fontSize="10" fill="#00b863" letterSpacing="1">
              core_ml
            </text>
            <text x="660" y="320" fontFamily="Share Tech Mono" fontSize="10" fill="#b87a00" letterSpacing="1">
              re_rank
            </text>
            <text x="870" y="320" fontFamily="Share Tech Mono" fontSize="10" fill="#00b863" letterSpacing="1">
              explain
            </text>
            <text x="1080" y="320" fontFamily="Share Tech Mono" fontSize="10" fill="#4a4a44" letterSpacing="1">
              deliver
            </text>

            <line x1="20" y1="335" x2="1190" y2="335" stroke="#15161a" strokeWidth="1" />
          </svg>
        </div>
      </div>
    </section>
  );
}
