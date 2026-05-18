import { useEffect, useRef, useState } from 'react';

/**
 * Adds `.reveal` and (once visible) `.in` classes to an element.
 * Returns a ref to attach, plus a className string ready to spread.
 */
export function useScrollReveal(threshold = 0.1) {
  const ref = useRef(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) {
            setVisible(true);
            io.unobserve(e.target);
          }
        });
      },
      { threshold }
    );
    io.observe(el);
    return () => io.disconnect();
  }, [threshold]);

  const className = `reveal${visible ? ' in' : ''}`;
  return [ref, className];
}
