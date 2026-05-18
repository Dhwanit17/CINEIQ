import { datasets } from '../data/datasets.js';
import { useScrollReveal } from '../hooks/useScrollReveal.js';

function DataCard({ data }) {
  const [ref, cls] = useScrollReveal();
  const titleLines = data.title;

  return (
    <div ref={ref} className={`data-card ${cls}`}>
      <div className="data-card-head">
        <div className="data-id">{data.id}</div>
        <div className="data-status">
          <span className="dot"></span>INDEXED
        </div>
      </div>
      <h3>
        {titleLines.map((line, i) => (
          <span key={i}>
            {line}
            {i < titleLines.length - 1 && <br />}
          </span>
        ))}
      </h3>
      <div className="source">{data.source}</div>
      <p>{data.description}</p>
      <div className="data-stats">
        {data.stats.map((s) => (
          <div key={s.lbl} className="data-stat">
            <div className="num">{s.num}</div>
            <div className="lbl">{s.lbl}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function Datasets() {
  return (
    <section className="datasets" id="datasets">
      <div className="container">
        <div className="section-tag">§ 05 · Datasets</div>
        <h2 className="section-title">
          Built on <em>open</em> data.
        </h2>

        <div className="data-grid">
          {datasets.map((d) => (
            <DataCard key={d.id} data={d} />
          ))}
        </div>
      </div>
    </section>
  );
}
