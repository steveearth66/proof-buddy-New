import "../scss/_persistent-pad.scss";
import { useState, useEffect, useMemo, useRef, useCallback } from "react";
import useDoubleClick from "use-double-click";
import Col from "react-bootstrap/Col";
import { useCollapsing } from "../hooks/useCollapsing";

export default function PersistentPad({ equation, onHighlightChange, side }) {
  const [currentPosition, setCurrentPosition] = useState(0); // Starting position
  const [positionDict, setPositionDict] = useState({});
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
  const padRef = useRef(null);
  const {
    collapse,
    restore,
    findSelectionParenthesis,
    checkParenthesisConsistency,
    balanceParenthesis
  } = useCollapsing();
  //const posdict = window.sharedDict || {};
  //console.log("posdict: ", posdict);

  // place holder for the hardcoded dictionary
  // for (cons (if (= 2 3) 1 (+ (* 4 5) (* 6 7)) ) null)
 // console.log("sharedDict", window.sharedDict);
 // const posdict = useMemo(
 //   () => (window.sharedDict || {}),[]); // Steve's attempt to get the dictionary from useRacketRuleFields
  /*
  const hardcodedPositionDict = useMemo(
    () => ({ 0: [0, 1, 0, 0],1: [0, 1, 1, 4],4: [0, 5, 1, 14],5: [4, 5, 5, 11],11: [4, 11, 5, 11],
      14: [0, 15, 4, 30],15: [14, 15, 15, 17],17: [14, 18, 15, 26],18: [17, 18, 18, 20],
      20: [17, 20, 18, 22],22: [17, 22, 20, 22],26: [14, 26, 17, 26],30: [0, 31, 14, 30],
      31: [30, 31, 31, 33],33: [30, 34, 31, 43],34: [33, 34, 34, 36],36: [33, 36, 34, 39],
      39: [33, 39, 36, 39],43: [30, 44, 33, 43],44: [43, 44, 44, 46],46: [43, 46, 44, 49],
      49: [43, 49, 46, 49] }),[]);
      
  useEffect(() => {
    setPositionDict(posdict);
  }, [posdict]);
  console.log(posdict, positionDict);
*/
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
      handelHighlight(selectionRange);
    } catch (error) {
      console.error("Error while highlighting selection: ", error);
    }
  };

  const highlightWordOrNumber = () => {
    try {
      setHighlightedText("");
      
      // Check if there is a valid selection
      const selection = window.getSelection();
      if (!selection || selection.rangeCount === 0) {
        console.warn("No valid text selection found or empty selection.");
        return; // Exit if no valid range is found
      }
        
      const range = window.getSelection().getRangeAt(0);
      const startOffset = range.startOffset;
      const endOffset = range.endOffset;
      const selectionRange = { start: startOffset, end: endOffset };
      const start = selectionRange.start;
      const end = selectionRange.end;

      // Ensure the selection is within the expected element (e.g., padRef)
      if (!padRef.current.contains(range.commonAncestorContainer)) {
        console.warn("Selection is outside the text container.");
        return; // Exit if selection is not in the correct element
        }

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

  const handelHighlight = (selectionRange) => {
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

  const getStartIndex = (selectedText) => {
    return returnedText.indexOf(selectedText);
  };
/*
  const getEndIndex = (selectedText) => {
    return getStartIndex(selectedText) + selectedText.length;
  };
  */
  const getEndIndex = useCallback(
    (start) => {
      if (returnedText[start] === "(") {
        let stack = 1;
        for (let i = start + 1; i < returnedText.length; i++) {
          if (returnedText[i] === "(") stack++;
          else if (returnedText[i] === ")") stack--;
          if (stack === 0) return i;
        }
      }
      if (returnedText[start] === "'") {
        if (returnedText[start + 1] === "(") {
          let stack = 1;
          for (let i = start + 2; i < returnedText.length; i++) {
            if (returnedText[i] === "(") stack++;
            else if (returnedText[i] === ")") stack--;
            if (stack === 0) return i;
          }
        }
      }
      if (/^[a-zA-Z0-9]+$/.test(returnedText.substring(start))) {
        return returnedText.length - 1;
      }
      for (let i = start + 1; i < returnedText.length; i++) {
        if (!/^[a-zA-Z0-9]$/.test(returnedText[i])) {
          return i - 1;
        }
      }
      return returnedText.length - 1;
    },
    [returnedText]
  );

  const updateHighlight = useCallback(
    (position) => {
      const start = position;
      const end = getEndIndex(start);
      const highlightedText = returnedText.substring(start, end + 1);
      setHighlightedText(highlightedText);
      setSelectionRange({ start, end });
    },
    [getEndIndex, returnedText]
  );

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
/*
  // Arrow key navigation by GPT
  useEffect(() => {
    const handleArrowKey = (e) => {
      if (!positionDict[currentPosition]) return;

      let nextPosition = currentPosition;
      switch (e.key) {
        case "ArrowUp":
          nextPosition = positionDict[currentPosition][0];
          break;
        case "ArrowDown":
          nextPosition = positionDict[currentPosition][1];
          break;
        case "ArrowLeft":
          nextPosition = positionDict[currentPosition][2];
          break;
        case "ArrowRight":
          nextPosition = positionDict[currentPosition][3];
          break;
        default:
          return;
      }
      if (nextPosition !== currentPosition) {
        setCurrentPosition(nextPosition);
        updateHighlight(nextPosition);
      }
    };

    window.addEventListener("keydown", handleArrowKey);
    return () => {
      window.removeEventListener("keydown", handleArrowKey);
    };
  }, [currentPosition, posdict, positionDict, updateHighlight]);
*/
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
