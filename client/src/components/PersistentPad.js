import "../scss/_persistent-pad.scss";
import { useState, useEffect, useRef, useCallback } from "react";
import useDoubleClick from "use-double-click";
import Col from "react-bootstrap/Col";
import { useCollapsing } from "../hooks/useCollapsing";

export default function PersistentPad({ equation, onHighlightChange, side, legalStartPositions }) {
  const [highlightedText, setHighlightedText] = useState("");
  const [selectionRange, setSelectionRange] = useState({ start: 0, end: 0 });
  const [controlPressed, setControlPressed] = useState(false);
  const [restorePressed, setRestoredPress] = useState(false);
  const [collapsed, setCollapsed] = useState(null);
  const [returnedText, setReturnedText] = useState(equation);
  const [collapsedSelection, setCollapsedSelection] = useState({
    start: 0,
    end: 0
  });
  const [positionTracker, setPositionTracker] = useState(null);
  const padRef = useRef(null);
  const {
    collapse,
    restore,
    findSelectionParenthesis,
    checkParenthesisConsistency,
    balanceParenthesis,
    findSelection
  } = useCollapsing();

  useDoubleClick({
    onSingleClick: (e) => {
      e.stopPropagation();
      e.preventDefault();
      if (!controlPressed && !restorePressed) highlightWordOrNumber();
      if (controlPressed && !restorePressed) doCollapse();
      if (restorePressed && !controlPressed) restoreCollapse();
    },
    onDoubleClick: (e) => {
      setControlPressed(false);
      setRestoredPress(false);
      e.stopPropagation();
      e.preventDefault();
      handelSelection();
    },
    ref: padRef,
    latency: 250
  });

  const doCollapse = () => {
    try {
      const range = window.getSelection().getRangeAt(0);
      const startOffset = range.startOffset;
      const endOffset = range.endOffset;

      const selectionRange = { start: startOffset, end: endOffset };
      const { result, collapseRange } = collapse(returnedText, selectionRange);
      setCollapsed(result);
      setCollapsedSelection(collapseRange);
    } catch (error) {
      console.error("Error collapsing brackets: ", error);
    }
  };

  const restoreCollapse = () => {
    try {
      const range = window.getSelection().getRangeAt(0);
      const startOffset = range.startOffset;
      const endOffset = range.endOffset;

      const selectionRange = { start: startOffset, end: endOffset };
      const { result } = restore(collapsed, selectionRange);
      setCollapsed(result);
    } catch (error) {
      console.error("Error restoring brackets: ", error);
    }
  };

  const handelSelection = () => {
    try {
      setHighlightedText("");
      const range = window.getSelection().getRangeAt(0);
      const startOffset = range.startOffset;
      const endOffset = range.endOffset;

      const selectionRange = { start: startOffset, end: endOffset };
      handelClickingHighlight(selectionRange);
    } catch (error) {
      console.error("Error while highlighting selection: ", error);
    }
  };

  const highlightWordOrNumber = () => {
    try {
      setHighlightedText("");
      const range = window.getSelection().getRangeAt(0);
      const startOffset = range.startOffset;
      const endOffset = range.endOffset;

      const selectionRange = { start: startOffset, end: endOffset };
      const start = selectionRange.start;
      const end = selectionRange.end;

      let startWord = start;
      while (startWord > 0 && !returnedText[startWord - 1].match(/\s|\(/)) {
        startWord--;
      }

      let endWord = end;
      while (
        endWord < returnedText.length &&
        !returnedText[endWord].match(/\s|\)/)
      ) {
        endWord++;
      }

      const highlightedText = returnedText.substring(startWord, endWord);
      setHighlightedText(highlightedText);
      onHighlightChange(startWord);
      setSelectionRange({
        start: startWord,
        end: endWord
      });
    } catch (error) {
      console.error("Error while highlighting word: ", error);
    }
  };

  const handelClickingHighlight = (selectionRange) => {
    const selectedPart = findSelectionParenthesis(returnedText, selectionRange);
    if (!checkParenthesisConsistency(selectedPart)) {
      const highlighted = checkAndGetQuotient(
        balanceParenthesis(returnedText, selectedPart)
      );
      setHighlightedText(highlighted);
      onHighlightChange(getStartIndex(highlighted));
      setSelectionRange({
        start: getStartIndex(highlighted),
        end: getEndIndex(highlighted)
      });
    } else {
      const highlighted = checkAndGetQuotient(selectedPart);
      setHighlightedText(highlighted);
      onHighlightChange(getStartIndex(highlighted));
      setSelectionRange({
        start: getStartIndex(highlighted),
        end: getEndIndex(highlighted)
      });
    }
  };

  const handelHighlight = (startPosition) => {
    const selectedPart = findSelection(returnedText, startPosition);

    if (!checkParenthesisConsistency(selectedPart)) {
      const highlighted = checkAndGetQuotient(
        balanceParenthesis(returnedText, selectedPart)
      );
      setHighlightedText(highlighted);
      onHighlightChange(getStartIndex(highlighted));
      setSelectionRange({
        start: getStartIndex(highlighted),
        end: getEndIndex(highlighted)
      });
    } else {
      const highlighted = checkAndGetQuotient(selectedPart);
      setHighlightedText(highlighted);
      onHighlightChange(getStartIndex(highlighted));
      setSelectionRange({
        start: getStartIndex(highlighted),
        end: getEndIndex(highlighted)
      });
    }
  };

  const getStartIndex = (selectedText) => {
    return returnedText.indexOf(selectedText);
  };

  const getEndIndex = (selectedText) => {
    return getStartIndex(selectedText) + selectedText.length;
  };

  const checkAndGetQuotient = (selectedText) => {
    const start = returnedText.indexOf(selectedText);
    const end = start + selectedText.length;

    if (returnedText[start - 1] === "'") {
      const quotient = returnedText.substring(start - 1, end);
      return quotient;
    } else {
      return selectedText;
    }
  };

  const clearHighlight = (e) => {
    e.preventDefault();
    setHighlightedText("");

    onHighlightChange(-1);
    const savedHighlights = JSON.parse(
      sessionStorage.getItem("highlights") || "[]"
    );
    const newHighlights = savedHighlights.filter(
      (highlight) =>
        !(highlight.equation === equation && highlight.side === side)
    );
    sessionStorage.setItem("highlights", JSON.stringify(newHighlights));
  };

  const replaceSelection = useCallback(
    (equation, selectionRange, replacement) => {
      const start = selectionRange.start;
      const end = selectionRange.end;
      const beforeSelection = equation.substring(0, start);
      const afterSelection = equation.substring(end);
      return (
        beforeSelection +
        `<span class="highlight">${replacement}</span>` +
        afterSelection
      );
    },
    []
  );

  const initializePositionTracker = (startingIndex) => {
    const currentIndex = startingIndex;
    const nextIndex = (currentIndex + 1) % legalStartPositions.length;
    const previousIndex = (currentIndex - 1 + legalStartPositions.length) % legalStartPositions.length;

    return {
      previousIndex,
      currentIndex,
      nextIndex
    }
  };

  const handelRightArrowPressed = () => {
    setPositionTracker((prev) => {
      if (!prev) {
        return initializePositionTracker(0);
      }
      
      const currentIndex = (prev.currentIndex + 1) % legalStartPositions.length;
      const nextIndex = (prev.nextIndex + 1) % legalStartPositions.length;
      const previousIndex = prev.currentIndex;

      handelHighlight(legalStartPositions[currentIndex]);

      return {
        previousIndex,
        currentIndex,
        nextIndex
      };
    })
  };

  const handelLeftArrowPressed = () => {
    setPositionTracker((prev) => {
      if (!prev) {
        return initializePositionTracker(legalStartPositions.length - 1);
      }

      const currentIndex = (prev.currentIndex - 1 + legalStartPositions.length) % legalStartPositions.length;
      const nextIndex = prev.currentIndex;
      const previousIndex = (prev.previousIndex - 1 + legalStartPositions.length) % legalStartPositions.length;

      handelHighlight(legalStartPositions[currentIndex]);

      return {
        previousIndex,
        currentIndex,
        nextIndex
      }
    });
  }

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
        selectionRange,
        collapsed
      });
      sessionStorage.setItem("highlights", JSON.stringify(savedHighlights));
    };

    if (highlightedText || collapsed) {
      saveHighlightToSession(highlightedText);
    }
  }, [highlightedText, side, selectionRange, equation, collapsed]);

  useEffect(() => {
    const savedHighlights = JSON.parse(
      sessionStorage.getItem("highlights") || "[]"
    );

    savedHighlights.forEach((highlight) => {
      if (highlight.equation === equation && highlight.side === side) {
        setHighlightedText(highlight.highlightedText);
        setSelectionRange(highlight.selectionRange);
        setCollapsed(highlight.collapsed);
      }
    });
  }, [equation, side]);

  useEffect(() => {
    const keyEvent = (e) => {
      if (e.key === "Control") {
        setControlPressed(true);
      }
      if (e.key === "Alt") {
        setRestoredPress(true);
      }
      if (e.key === "ArrowRight") {
        handelRightArrowPressed();
      } 
      if (e.key === "ArrowLeft") {
        handelLeftArrowPressed();
      }
    };

    const keyEventUp = (e) => {
      if (e.key === "Control") {
        setControlPressed(false);
      }
      if (e.key === "Alt") {
        setRestoredPress(false);
      }
    };

    window.addEventListener("keydown", keyEvent);
    window.addEventListener("keyup", keyEventUp);

    return () => {
      window.removeEventListener("keydown", keyEvent);
      window.removeEventListener("keyup", keyEventUp);
    };
    // eslint-disable-next-line
  }, []);

  useEffect(() => {
    if (collapsed === equation) {
      setCollapsed(null);
    }
  }, [collapsed, equation]);

  useEffect(() => {
    if (collapsed) {
      setReturnedText(collapsed);
    } else {
      setReturnedText(equation);
    }
    if (highlightedText) {
      if (collapsed) {
        setReturnedText(
          replaceSelection(collapsed, selectionRange, highlightedText)
        );
      } else {
        setReturnedText(
          replaceSelection(equation, selectionRange, highlightedText)
        );
      }
    }
  }, [
    collapsed,
    highlightedText,
    equation,
    replaceSelection,
    selectionRange,
    collapsedSelection
  ]);

  return (
    <Col xs={8}>
      <p
        ref={padRef}
        onContextMenu={clearHighlight}
        dangerouslySetInnerHTML={{
          __html: returnedText
        }}
        className="pad"
      />
    </Col>
  );
}
