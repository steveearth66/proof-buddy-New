import "../scss/_persistent-pad.scss";
import { useState, useEffect, useRef, useCallback } from "react";
import Col from "react-bootstrap/Col";
import DivMakerComponent from "./divMaker"; // Steve's addition based on Galen's idea
import React, { useImperativeHandle, forwardRef } from "react";

const PersistentPad = forwardRef(function PersistentPad({ equation, onHighlightChange, side, jsonTree, lineNum, editableLineNum, startPosition, ...props }, ref) {
  // attempting to console log the jsonTree
  //console.log("jsonTree rep:", jsonTree)
  const [highlightedText, setHighlightedText] = useState("");
  const [selectionRange, setSelectionRange] = useState({ start: 0, end: 0 });
  const [selected, setSelected] = useState(startPosition); // changing selected from node to it's ID

  const lineNumRef = useRef(lineNum); // Store the initial lineNum in a ref

  let origTree = jsonTree; // will this save tree? is having const bad if it changes later for next racket expr?

  // Expose moveSelection and focus to parent
  useImperativeHandle(ref, () => ({
    moveSelection,
    focus: () => padDivRef.current && padDivRef.current.focus()
  }));

  useEffect(() => {
    const saveHighlightToSession = (highlightedText) => {
      const savedHighlights = JSON.parse(
        sessionStorage.getItem("highlights") || "[]"
      );

      savedHighlights.forEach((highlight, index) => {
        if (highlight.equation === equation && highlight.side === side) {
          savedHighlights.splice(index, 1);
        }
      });

      savedHighlights.push({
        equation,
        highlightedText,
        side,
        selectionRange
      });
      sessionStorage.setItem("highlights", JSON.stringify(savedHighlights));
    };

    if (highlightedText) {
      saveHighlightToSession(highlightedText);
    }
  }, [highlightedText, side, selectionRange, equation]);

  useEffect(() => {
    const savedHighlights = JSON.parse(
      sessionStorage.getItem("highlights") || "[]"
    );

    savedHighlights.forEach((highlight) => {
      if (highlight.equation === equation && highlight.side === side) {
        setHighlightedText(highlight.highlightedText);
        setSelectionRange(highlight.selectionRange);
      }
    });
  }, [equation, side]);

const moveSelection = useCallback((direction) => {
	let newSelected = selected; //defaulting to currNode

  if (direction === "up") {
    newSelected = origTree[newSelected].parent ?? newSelected;
  } else if (direction === "down") {
    newSelected = origTree[newSelected].children[0] ?? newSelected;
  } else if (direction === "left") {
    newSelected = origTree[newSelected].leftSib ?? newSelected;
  } else if (direction === "right") {
    newSelected = origTree[newSelected].rightSib ?? newSelected;
  }

  onHighlightChange(newSelected);
  setSelected(newSelected);

}, [selected, origTree, onHighlightChange]);

 const padDivRef = useRef(null);

  // Expose moveSelection and focus to parent
  useImperativeHandle(ref, () => ({
    moveSelection,
    focus: () => padDivRef.current && padDivRef.current.focus()
  }));

return (
  <Col xs={8}>
    <div
      id={`persistent-pad-${lineNumRef.current}`}
      ref={padDivRef}
      tabIndex={0}
      {...props}
    >
      <DivMakerComponent expr={jsonTree} selected={selected} origTree={origTree} lineNumber={lineNumRef.current} />
    </div>
  </Col>
);
});
export default PersistentPad;