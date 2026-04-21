import { useState, useRef, useEffect } from 'react';

interface ShowMoreTextProps {
  text: string;
  lines?: number;
  className?: string;
}

export function ShowMoreText({ text, lines = 2, className = '' }: ShowMoreTextProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isOverflowing, setIsOverflowing] = useState(false);
  const textRef = useRef<HTMLParagraphElement>(null);

  useEffect(() => {
    const checkOverflow = () => {
      if (textRef.current) {
        // Reset overflow to check actual size
        const el = textRef.current;
        const currentOverflow = el.scrollHeight > el.clientHeight;
        setIsOverflowing(currentOverflow);
      }
    };
    
    checkOverflow();
    window.addEventListener('resize', checkOverflow);
    return () => window.removeEventListener('resize', checkOverflow);
  }, [text, lines]);

  if (!text) return null;

  return (
    <div className={`space-y-1 ${className}`}>
      <p
        ref={textRef}
        className={`text-sm text-gray-500 whitespace-pre-wrap ${
          !isExpanded ? `line-clamp-${lines}` : ''
        }`}
        style={!isExpanded ? { display: '-webkit-box', WebkitLineClamp: lines, WebkitBoxOrient: 'vertical', overflow: 'hidden' } : {}}
      >
        {text}
      </p>
      {isOverflowing && !isExpanded && (
        <button
          onClick={() => setIsExpanded(true)}
          className="text-xs font-semibold text-blue-600 hover:text-blue-800 transition-colors"
        >
          Show more
        </button>
      )}
      {isExpanded && (
        <button
          onClick={() => setIsExpanded(false)}
          className="text-xs font-semibold text-gray-500 hover:text-gray-700 transition-colors"
        >
          Show less
        </button>
      )}
    </div>
  );
}
