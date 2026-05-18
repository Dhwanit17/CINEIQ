import { useScrollNav } from '../hooks/useScrollNav.js';

const NAV_LINKS = [
  { id: 'problem', label: 'Problem' },
  { id: 'features', label: 'How It Works' },
  { id: 'demo', label: 'Demo' },
  { id: 'datasets', label: 'Data' },
  { id: 'arch', label: 'Architecture' },
];

const SECTION_IDS = NAV_LINKS.map((l) => l.id);

export default function Nav() {
  const { scrolled, activeId } = useScrollNav(SECTION_IDS);

  return (
    <nav className={`topnav${scrolled ? ' scrolled' : ''}`} id="topnav">
      <a href="#hero" className="logo">
        CINE<span className="dot">▮</span>IQ
      </a>
      <ul className="navlinks">
        {NAV_LINKS.map((link) => (
          <li key={link.id}>
            <a
              href={`#${link.id}`}
              className={activeId === link.id ? 'active' : ''}
            >
              {link.label}
            </a>
          </li>
        ))}
      </ul>
      <div className="nav-status">
        <span className="live">●</span> SYSTEM_LIVE · V0.4.2
      </div>
    </nav>
  );
}
