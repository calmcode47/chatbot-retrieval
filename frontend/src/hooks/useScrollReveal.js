import { useEffect } from 'react';

export function useScrollReveal(activePage, rootMargin = '0px 0px -70px 0px') {
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          observer.unobserve(entry.target);
        }
      }),
      { rootMargin, threshold: 0.08 }
    );
    
    // Query elements after a short frame to ensure the page has mounted
    const frame = requestAnimationFrame(() => {
      document.querySelectorAll('.reveal').forEach(el => observer.observe(el));
    });

    return () => {
      cancelAnimationFrame(frame);
      observer.disconnect();
    };
  }, [activePage, rootMargin]);
}
