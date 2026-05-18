import { features } from '../data/features.js';
import { useScrollReveal } from '../hooks/useScrollReveal.js';

function FeatureCard({ feature }) {
  const [ref, cls] = useScrollReveal();
  const titleLines = feature.title;

  return (
    <div ref={ref} className={`feature ${cls}`}>
      <div className="feature-head">
        <div className="feature-icon">{feature.icon}</div>
        <div className="feature-num">{feature.num}</div>
      </div>
      <h3>
        {titleLines.map((line, i) => (
          <span key={i}>
            {line}
            {i < titleLines.length - 1 && <br />}
          </span>
        ))}
      </h3>
      <p>
        {feature.bodyParts
          ? feature.bodyParts.map((part, i) =>
              typeof part === 'string' ? (
                part
              ) : (
                <em
                  key={i}
                  style={{ color: 'var(--amber)', fontStyle: 'normal' }}
                >
                  {part.em}
                </em>
              )
            )
          : feature.body}
      </p>
      <div className="feature-tech">
        {feature.tags.map((tag) => (
          <span key={tag} className="tech-tag">
            {tag}
          </span>
        ))}
      </div>
    </div>
  );
}

export default function Features() {
  return (
    <section className="features" id="features">
      <div className="container">
        <div className="section-tag">§ 02 · Deliverables</div>
        <h2 className="section-title">
          How <em>CINEIQ</em> Works.
        </h2>

        <div className="features-grid">
          {features.map((f) => (
            <FeatureCard key={f.num} feature={f} />
          ))}
        </div>
      </div>
    </section>
  );
}
