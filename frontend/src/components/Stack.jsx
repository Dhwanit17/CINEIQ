import { stackColumns } from '../data/stack.js';
import { useScrollReveal } from '../hooks/useScrollReveal.js';

function StackCol({ col }) {
  const [ref, cls] = useScrollReveal();
  return (
    <div ref={ref} className={`stack-col ${cls}`}>
      <h4>{col.label}</h4>
      <div className="stack-num">{col.num}</div>
      <div className="stack-tags">
        {col.pills.map((pill) => (
          <span key={pill} className="stack-pill">
            {pill}
          </span>
        ))}
      </div>
    </div>
  );
}

export default function Stack() {
  return (
    <section className="stack" id="stack">
      <div className="container">
        <div className="section-tag">§ 04 · Tech Stack</div>
        <h2 className="section-title">
          <em>Open</em> tools. No magic.
        </h2>

        <div className="stack-grid">
          {stackColumns.map((col) => (
            <StackCol key={col.num} col={col} />
          ))}
        </div>
      </div>
    </section>
  );
}
