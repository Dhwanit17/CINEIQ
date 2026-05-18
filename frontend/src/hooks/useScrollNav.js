import { useEffect, useState } from 'react';

/**
 * Tracks page scroll to determine:
 *  - whether the nav should show its "scrolled" background
 *  - which section id is currently active in the viewport
 */
export function useScrollNav(sectionIds) {
  const [scrolled, setScrolled] = useState(false);
  const [activeId, setActiveId] = useState(null);

  useEffect(() => {
    const onScroll = () => {
      setScrolled(window.scrollY > 40);

      const y = window.scrollY + 120;
      let nextActive = null;
      for (const id of sectionIds) {
        const el = document.getElementById(id);
        if (el && el.offsetTop <= y) {
          nextActive = id;
        }
      }
      setActiveId(nextActive);
    };

    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, [sectionIds]);

  return { scrolled, activeId };
}
