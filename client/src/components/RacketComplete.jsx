import React, { useEffect, useState } from "react";
import Confetti from "react-confetti";
import "../scss/_racket-complete.scss";

export default function RacketComplete() {
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
    <div className="confetti-overlay">
      <h1>Racket Complete!!!!!!!!</h1>
      <Confetti width={width} height={height} />
    </div>
  );
}
