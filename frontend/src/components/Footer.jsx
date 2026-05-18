const FOOTER_COLS = [
  {
    heading: '// Project',
    links: ['GitHub', 'Docs', 'Roadmap', 'Changelog'],
  },
  {
    heading: '// API',
    links: ['/recommend', '/similar', '/explain', '/dashboard'],
  },
  {
    heading: '// Community',
    links: ['Discord', 'Blog', 'Papers', 'Contact'],
  },
];

export default function Footer() {
  return (
    <footer>
      <div className="footer-grid">
        <div className="footer-brand">
          <a href="#hero" className="logo">
            CINE<span className="dot">▮</span>IQ
          </a>
          <p>
            An open, explainable movie recommendation engine. Built because content discovery
            deserves transparency.
          </p>
          <div className="tag">// Built with open data. No black boxes.</div>
        </div>

        {FOOTER_COLS.map((col) => (
          <div key={col.heading} className="footer-col">
            <h5>{col.heading}</h5>
            <ul>
              {col.links.map((link) => (
                <li key={link}>
                  <a href="#">{link}</a>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>

      <div className="footer-bottom">
        <div>© 2026 CINEIQ · MIT LICENSE · NO TRACKING</div>
        <div>
          <span className="blink">●</span> SYSTEM_OK · UPTIME 99.97%
        </div>
      </div>
    </footer>
  );
}
