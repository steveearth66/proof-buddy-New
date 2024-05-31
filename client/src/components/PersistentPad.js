import "../scss/_persistent-pad.scss";
import { useState, useEffect, useRef } from "react";
import useDoubleClick from "use-double-click";
import Col from "react-bootstrap/Col";
import { useCollapsing } from "../hooks/useCollapsing";

export default function PersistentPad({ equation, onHighlightChange, side }) {
  const [highlightedText, setHighlightedText] = useState("");
  const [selectionRange, setSelectionRange] = useState({ start: 0, end: 0 });
  const [controlPressed, setControlPressed] = useState(false);
  const padRef = useRef(null);
  const {
    handleCollapsing,
    findSelectionParenthesis,
    checkParenthesisConsistency,
    balanceParenthesis
  } = useCollapsing();

  useDoubleClick({
    onSingleClick: (e) => {
      e.stopPropagation();
      e.preventDefault();
      highlightWordOrNumber();
    },
    onDoubleClick: (e) => {
      e.stopPropagation();
      e.preventDefault();
      if (!controlPressed) {
        handelSelection();
      }
      if (controlPressed) {
        console.log("Ctrl + Double Click");
        doCollapse();
      }
    },
    ref: padRef,
    latency: 250
  });

  const doCollapse = () => {
    const range = window.getSelection().getRangeAt(0);
    const startOffset = range.startOffset;
    const endOffset = range.endOffset;

    const selectionRange = { start: startOffset, end: endOffset };
    console.log(handleCollapsing(equation, selectionRange));
  };

  const handelSelection = () => {
    try {
      setHighlightedText("");
      const range = window.getSelection().getRangeAt(0);
      const startOffset = range.startOffset;
      const endOffset = range.endOffset;

      const selectionRange = { start: startOffset, end: endOffset };
      handelHighlight(selectionRange);
    } catch (error) {
      console.error("Error while highlighting selection: ", error);
    }
  };

  const highlightWordOrNumber = () => {
    setHighlightedText("");
    const range = window.getSelection().getRangeAt(0);
    const startOffset = range.startOffset;
    const endOffset = range.endOffset;

    const selectionRange = { start: startOffset, end: endOffset };
    const start = selectionRange.start;
    const end = selectionRange.end;

    let startWord = start;
    while (startWord > 0 && !equation[startWord - 1].match(/\s|\(/)) {
      startWord--;
    }

    let endWord = end;
    while (endWord < equation.length && !equation[endWord].match(/\s|\)/)) {
      endWord++;
    }

    const highlightedText = equation.substring(startWord, endWord);
    setHighlightedText(highlightedText);
    onHighlightChange(startWord);
    setSelectionRange({
      start: startWord,
      end: endWord
    });
  };

  const handelHighlight = (selectionRange) => {
    const selectedPart = findSelectionParenthesis(equation, selectionRange);
    if (!checkParenthesisConsistency(selectedPart)) {
      const highlighted = checkAndGetQuotient(
        balanceParenthesis(equation, selectedPart)
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
    return equation.indexOf(selectedText);
  };

  const getEndIndex = (selectedText) => {
    return getStartIndex(selectedText) + selectedText.length;
  };

  const checkAndGetQuotient = (selectedText) => {
    const start = equation.indexOf(selectedText);
    const end = start + selectedText.length;

    if (equation[start - 1] === "'") {
      const quotient = equation.substring(start - 1, end);
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

  const replaceSelection = (selectionRange, replacement) => {
    const start = selectionRange.start;
    const end = selectionRange.end;
    const beforeSelection = equation.substring(0, start);
    const afterSelection = equation.substring(end);
    return (
      beforeSelection +
      `<span class="highlight">${replacement}</span>` +
      afterSelection
    );
  };

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

      savedHighlights.push({ equation, highlightedText, side, selectionRange });
      sessionStorage.setItem("highlights", JSON.stringify(savedHighlights));
    };

    if (highlightedText) {
      saveHighlightToSession(highlightedText);
    }
  }, [highlightedText, equation, side, selectionRange]);

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

  useEffect(() => {
    const keyEvent = (e) => {
      if (e.key === "Control") {
        setControlPressed(true);
      }
    };

    const keyEventUp = (e) => {
      if (e.key === "Control") {
        setControlPressed(false);
      }
    };

    window.addEventListener("keydown", keyEvent);
    window.addEventListener("keyup", keyEventUp);

    return () => {
      window.removeEventListener("keydown", keyEvent);
      window.removeEventListener("keyup", keyEventUp);
    };
  }, []);

  return (
    <Col xs={8}>
      <p
        ref={padRef}
        onContextMenu={clearHighlight}
        dangerouslySetInnerHTML={{
          __html: highlightedText
            ? replaceSelection(selectionRange, highlightedText)
            : equation
        }}
        className="pad"
      />
    </Col>
  );
}
