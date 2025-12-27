'use client';

export default function ScrollIndicator() {
  const scrollToNext = () => {
    const sections = document.querySelectorAll('.snap-section');
    const currentScroll = window.scrollY;
    
    for (let i = 0; i < sections.length; i++) {
      const section = sections[i] as HTMLElement;
      const sectionTop = section.offsetTop;
      
      if (sectionTop > currentScroll + 100) {
        window.scrollTo({
          top: sectionTop,
          behavior: 'smooth'
        });
        break;
      }
    }
  };

  return (
    <button
      onClick={scrollToNext}
      className="fixed bottom-8 left-1/2 -translate-x-1/2 z-40 animate-bounce opacity-50 hover:opacity-100 transition-opacity duration-200"
      aria-label="Scroll to next section"
    >
      <svg
        className="w-8 h-8 text-primary"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M19 9l-7 7-7-7"
        />
      </svg>
    </button>
  );
}
