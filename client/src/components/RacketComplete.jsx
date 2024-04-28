import React from "react";
import Confetti from "react-confetti";
import { useWindowSize } from "react-use";
import "../scss/_racket-complete.scss";

export default function RacketComplete() {
  const { width, height } = useWindowSize();

  return (
    <div className="confetti-overlay">
      <h1>Racket Complete!!!!!!!!</h1>
      <Confetti width={width} height={height} />
    </div>
  );
}
