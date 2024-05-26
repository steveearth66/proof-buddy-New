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
  const { handleCollapsing } = useCollapsing();

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
      doCollapse();
      console.log("Ctrl + Double Click");
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
    const selectedPart = findSelectionParenthesis(selectionRange);
    if (!checkParenthesisConsistency(selectedPart)) {
      const highlighted = checkAndGetQuotient(balanceParenthesis(selectedPart));
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

  const findSelectionParenthesis = (selectionRange) => {
    const start = selectionRange.start;
    const end = selectionRange.end;
    let openParenthesisIndex = -1;
    let closeParenthesisIndex = -1;

    for (let i = start; i >= 0; i--) {
      if (equation[i] === "(") {
        openParenthesisIndex = i;
        break;
      }
    }

    for (let i = end; i < equation.length; i++) {
      if (equation[i] === ")") {
        closeParenthesisIndex = i;
        break;
      }
    }

    if (openParenthesisIndex !== -1 && closeParenthesisIndex !== -1) {
      return equation.substring(
        openParenthesisIndex,
        closeParenthesisIndex + 1
      );
    }
  };

  const checkParenthesisConsistency = (selectedText) => {
    if (!selectedText) {
      return;
    }

    const stack = [];

    for (let i = 0; i < selectedText.length; i++) {
      const char = selectedText[i];
      if (char === "(") {
        stack.push(char);
      } else if (char === ")") {
        if (stack.length === 0) {
          return false; // More closing parentheses than opening ones
        }
        stack.pop();
      }
    }

    return stack.length === 0; // Return true if stack is empty, false otherwise
  };

  const balanceParenthesis = (selectedText) => {
    const stack = [];

    // Find the starting index of the selected text in the equation
    const startIndex = equation.indexOf(selectedText);
    if (startIndex === -1) {
      // Selected text not found in equation
      return selectedText;
    }

    // Find the start index of the expression containing the selected text
    let start = startIndex;
    while (start > 0 && equation[start] !== "(") {
      start--;
    }

    // Find the end index of the expression containing the selected text
    let end = startIndex + selectedText.length;
    while (end < equation.length && equation[end] !== ")") {
      end++;
    }

    // Extract the entire expression containing the selected text
    let expression = equation.substring(start, end + 1);

    if (!checkParenthesisConsistency(expression)) {
      expression = balanceParenthesis(expression);
    }

    // Push opening parentheses onto the stack
    for (let i = 0; i < expression.length; i++) {
      const char = expression[i];
      if (char === "(") {
        stack.push(char);
      } else if (char === ")") {
        if (stack.length === 0) {
          // Add an opening parenthesis to balance
          expression = expression.slice(0, i) + "(" + expression.slice(i);
          stack.push("(");
        } else {
          stack.pop();
        }
      }
    }

    // Add missing closing parentheses to balance
    while (stack.length > 0) {
      expression += ")";
      stack.pop();
    }
    return expression;
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
      if (e.key === "Control" && e.key === "m") {
        console.log("Ctrl + m pressed");
        setControlPressed(true);
      }
    };

    const keyEventUp = (e) => {
      if (e.key === "Control" && e.key === "m") {
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
