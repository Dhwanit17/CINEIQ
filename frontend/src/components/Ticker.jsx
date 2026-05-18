import { tickerData } from '../data/tickerData.js';

export default function Ticker() {
  // Duplicate the items for the seamless CSS animation loop.
  const passes = [0, 1];

  return (
    <div className="ticker">
      <div className="ticker-track" id="ticker-track">
        {passes.map((pass) =>
          tickerData.map((item, idx) => (
            <span key={`${pass}-${idx}`} className="ticker-item-group" style={{ display: 'contents' }}>
              <span className="ticker-item">
                <span className="yr">{item.y}</span>
                {item.t}
              </span>
              <span className="ticker-item sep">◆</span>
            </span>
          ))
        )}
      </div>
    </div>
  );
}
