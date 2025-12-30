import React, { useEffect, useState } from "react";
import Confetti from "react-confetti";
import "../scss/_racket-complete.scss";

export default function ProofComplete({ onDismiss }) {
  const [width, setWidth] = useState(window.innerWidth);
  const [height, setHeight] = useState(window.innerHeight);

  useEffect(() => {
    const handleResize = () => {
      setWidth(window.innerWidth);
      setHeight(window.innerHeight);
    };
    window.addEventListener("resize", handleResize);
    return () => {
      window.removeEventListener("resize", handleResize);
    };
  }, []);

  return (
    <div className="confetti-overlay" onClick={onDismiss} style={{ cursor: 'pointer' }}>
      <h1>Proof Complete!!!!!!!!</h1>
      <p style={{ fontSize: '1.2rem', marginTop: '1rem' }}>Click anywhere to dismiss</p>
      <Confetti width={width} height={height} />
    </div>
  );
}
