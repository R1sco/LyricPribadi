import React from 'react';

interface LyricsCardProps {
  lyrics: string;
}

const LyricsCard: React.FC<LyricsCardProps> = ({ lyrics }) => (
  <div className="card lyrics-card">
    <div className="card-body">
      <div className="lyrics-text">
        {lyrics.split('\n\n')
          .filter(paragraph => paragraph.trim() !== '')
          .map((paragraph, idx) => (
            <p key={idx}>{paragraph}</p>
          ))}
      </div>
    </div>
  </div>
);

export default LyricsCard;
