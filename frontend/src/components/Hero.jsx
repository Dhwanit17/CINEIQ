import { useMemo } from 'react';
import Ticker from './Ticker.jsx';

const DUST_COUNT = 40;

export default function Hero() {
  // Generate dust particles once with random positions/timings
  const dust = useMemo(
    () =>
      Array.from({ length: DUST_COUNT }, () => ({
        left: `${Math.random() * 100}%`,
        animationDelay: `${Math.random() * 20}s`,
        animationDuration: `${15 + Math.random() * 15}s`,
        opacity: 0.15 + Math.random() * 0.35,
      })),
    []
  );

  return (
    <section className="hero" id="hero">
      <div className="hero-dust" aria-hidden="true">
        {dust.map((style, i) => (
          <span key={i} style={style} />
        ))}
      </div>

      <div className="match-badge">
        AI MATCH SCORE
        <span className="num">95%</span>
      </div>

      <div className="hero-container">
        <div className="hero-meta-top">
          <span className="pulse"></span>
          <span>BOOTING RECOMMENDATION KERNEL · 2026.05.16</span>
        </div>

        <div className="wordmark-wrap">
          <h1 className="wordmark">
            <span className="glitch" data-text="CINE">
              CINE
            </span>
            <span>IQ</span>
          </h1>
        </div>

        <p className="tagline">
          <em>Open.</em>
          <span className="sep">/</span>
          <em>Explainable.</em>
          <span className="sep">/</span>
          <em>Yours.</em>
        </p>

        <div className="hero-genres">
          <span className="genre-pill accent">[SCI-FI]</span>
          <span className="genre-pill accent">[THRILLER]</span>
          <span className="genre-pill">[MIND-BENDING]</span>
          <span className="genre-pill">[NEO-NOIR]</span>
          <span className="genre-pill">[ARTHOUSE]</span>
        </div>

        <div className="hero-progress">
          <div className="hero-progress-label">
            <span>CONTINUE WATCHING · INCEPTION</span>
            <span>45:12 / 2:28:00</span>
          </div>
          <div className="hero-progress-bar"></div>
        </div>

        <div className="hero-cta">
          <a href="#demo" className="btn btn-primary">
            Get Recommendations
          </a>
          <a href="#arch" className="btn btn-ghost">
            View Source
          </a>
        </div>
      </div>

      <Ticker />
    </section>
  );
}
