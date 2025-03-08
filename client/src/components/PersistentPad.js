import "../scss/_persistent-pad.scss";
import { useState, useEffect, useRef, useCallback } from "react";
import useDoubleClick from "use-double-click";
import Col from "react-bootstrap/Col";
import { useCollapsing } from "../hooks/useCollapsing";
import makeDivs from "./divMaker"; //Steve's addition based on Galen's idea

export default function PersistentPad({ equation, onHighlightChange, side, jsonTree }) {
  // attempting to console log the jsonTree
  //console.log("jsonTree rep:", jsonTree)
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
  // Bob - adding in two new variables for arrow key navigation
  //const [expr, setExpr] = useState(null);
  const [selected, setSelected] = useState(jsonTree);
  const padRef = useRef(null);
  const {
    collapse,
    restore,
    findSelectionParenthesis,
    checkParenthesisConsistency,
    balanceParenthesis
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
      // may just be able to replace highlightedText function with data from the jsonTree rep....
      const highlightedText = returnedText.substring(startWord, endWord);
      console.log("highlightedText: " + highlightedText);
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

  //  handle highlight function can probably remain the same...
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

  // this function probably becomes redundant
  const getStartIndex = (selectedText) => {
    return returnedText.indexOf(selectedText);
  };
  // this function probably becomes redundant
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
  //old highlighting. might be deprecated once switch to arrow controls
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
  //old highlighting. might be deprecated once switch to arrow controls
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

// Arrow Key Navigation
useEffect(() => {
  let handleKeyUp = (e) => {
    if (selected === null) {
      // should only happen on first render; might be unnecessary
      return;
    }
    if (e.key === "ArrowUp") {
      // up selects parent expression
      // if no parent, don't change
      setSelected((curSelected) =>
        curSelected.parent === null ? curSelected : curSelected.parent
      );
    } else if (e.key === "ArrowDown") {
      // down selects first child value/expression
      // if no children, don't change
      setSelected((curSelected) =>{
        console.log("step1 parent: "+ curSelected.parent),
        console.log("step1 children: "+ curSelected.children),
        curSelected.children.length === 0
          ? curSelected
          : curSelected.children[0];
        console.log("step2: "+ curSelected.toString());}
      );
      
    } else if (e.key === "ArrowLeft") {
      // left selects left sibling value/expression
      // if no left sib, don't change
      setSelected((curSelected) =>
        curSelected.leftSib === null ? curSelected : curSelected.leftSib
      );
    } else if (e.key === "ArrowRight") {
      // right selects right sibling value/expression
      // if no right sib, don't change
      setSelected((curSelected) =>
        curSelected.rightSib === null ? curSelected : curSelected.rightSib
      );
    }
  };
  document.addEventListener("keyup", handleKeyUp);
  //document.addEventListener("keyup", () => console.log("key up listener"));
  return () => {
    document.removeEventListener("keyup", handleKeyUp);
  };
}, [selected]);

// /*
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
// */

/*  
return (
    <Col xs={8}>
      <div ref={padRef} >
        {makeDivs(jsonTree)}
      </div>
    </Col>
  );
  */
};