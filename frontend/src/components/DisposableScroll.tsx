import React, { useState, useRef, useEffect } from 'react';
import './DisposableScroll.css';

interface DisposableScrollProps {
  children: React.ReactNode;
  threshold?: number;
  onDispose?: () => void;
  className?: string;
}

export const DisposableScroll: React.FC<DisposableScrollProps> = ({
  children,
  threshold = 0.8,
  onDispose,
  className = ''
}) => {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [isDisposed, setIsDisposed] = useState(false);

  const checkScrollPosition = () => {
    if (!scrollRef.current) return;
    
    const { scrollTop, scrollHeight, clientHeight } = scrollRef.current;
    const scrollPosition = (scrollTop + clientHeight) / scrollHeight;
    
    if (scrollPosition > threshold && !isDisposed) {
      setIsDisposed(true);
      onDispose?.();
      
      // Lock scroll position
      scrollRef.current.style.overflow = 'hidden';
      scrollRef.current.style.pointerEvents = 'none';
    }
  };

  useEffect(() => {
    const currentRef = scrollRef.current;
    if (!currentRef) return;

    currentRef.addEventListener('scroll', checkScrollPosition);
    
    // Check initial position
    checkScrollPosition();
    
    return () => {
      currentRef.removeEventListener('scroll', checkScrollPosition);
    };
  }, [isDisposed, threshold]);

  return (
    <div 
      ref={scrollRef} 
      className={`disposable-scroll ${isDisposed ? 'disposed' : ''} ${className}`}
    >
      {children}
    </div>
  );
};
