import "../scss/_persistent-pad.scss";
import { useState, useEffect, useRef, useCallback, forwardRef } from "react";
import useDoubleClick from "use-double-click";
import Col from "react-bootstrap/Col";
import { useCollapsing } from "../hooks/useCollapsing";
import makeDivs from "./divMaker"; //Steve's addition based on Galen's idea

export default function PersistentPad ({ equation, onHighlightChange, side, jsonTree, shouldApplyKeyStroke, keyStroke, myIndex }) {
  // attempting to console log the jsonTree
  //console.log("jsonTree rep:", jsonTree);
  //console.log("jsonTree rep 0:", jsonTree[0])
  //console.log("jsonTree rep 0:", jsonTree[0][1])
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
  // initialize selected to 0 index
  const jsonTree_dict = jsonTree;
  //const equation_stored = equation
  console.log("jsonTree_dict: ", jsonTree_dict);
  //const [selected, setSelected] = useState(0);
  let selected = 0;
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
      //if (!controlPressed && !restorePressed) highlightWordOrNumber();
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
      setHighlightedText(equation);
      /*
      // Check if there is a valid selection
      const selection = window.getSelection();
      if (!selection || selection.rangeCount === 0) {
        console.warn("No valid text selection found or empty selection.");
        return; // Exit if no valid range is found
      }
      */
      const range = window.getSelection().getRangeAt(0);
      //attempting to switch start offset to selection
      //const startOffset = range.startOffset;
      //console.log("startOffset: " + startOffset);
      //const startOffset = selected;
      //const endOffset = range.endOffset;
      //console.log("endOffset: " + endOffset);
      const start_index = selected;
      console.log("start_index: " + start_index);
      const end_index = getEndIndex(start_index);
      console.log("end_index: " + end_index);
      // used selection Range use state instead of manual overwrite
      const selectionRange = { start: start_index, end: end_index };
      //const selectionRange = { start: start_index, end: end_index };
      const start = selectionRange.start;
      console.log("start: " + start);
      const end = selectionRange.end;

      //Ensure the selection is within the expected element (e.g., padRef)
      //console.log("Pad ref" + JSON.stringify(padRef.current));
      /*
      if (!padRef.current.contains(range.commonAncestorContainer)) {
        console.log("Pad ref" + JSON.stringify(padRef.current));
        console.log("Selection container: " + selectionRange.commonAncestorContainer);
        console.warn("Selection is outside the text container.");
        return; // Exit if selection is not in the correct element
        }
      */
      let startWord = start;
      console.log("startWord: " + startWord);
      console.log("equations is: " + equation)
      console.log("equation[startWord] is: "+ equation[startWord])
      //console.log("stored equation is: " + equation_stored)
      //console.log("startWord: " + startWord);
      // try replacing with equation
      /*
      while (startWord > 0 && !returnedText[startWord - 1].match(/\s|\(/)) {
        startWord--;
      }
        */
       // getting rid of startword - 1 temporarily
      while (startWord > 0 && !equation[startWord].match(/\s|\(/)) {
        startWord--;
      }

      let endWord = end;
      //console.log("endWord: " + endWord);
       // try replacing with equation
      /*
      while (
        endWord < returnedText.length &&
        !returnedText[endWord].match(/\s|\)/)
      ) {
        endWord++;
      }
        */
      while (
        endWord < equation.length &&
        !equation[endWord].match(/\s|\)/)
      ) {
        endWord++;
      }
      // may just be able to replace highlightedText function with data from the jsonTree rep....
      console.log("highlightedText before: " + highlightedText);
      // swapped replaceText for equation
      const newHighlightedValue = equation.substring(startWord, endWord);
      console.log("highlightedText: " + newHighlightedValue);
      setHighlightedText(newHighlightedValue);
      onHighlightChange(startWord);
      
      setSelectionRange({
        start: startWord,
        end: endWord
      });
      
    } catch (error) {
      console.error("Error while highlighting word: ", error);
    }
  };

  //  replace all instance of returnedText with equation
  /*
  const handelHighlight = (selectionRange) => {
    const selectedPart = findSelectionParenthesis(returnedText, selectionRange);
    if (!checkParenthesisConsistency(selectedPart)) {
      const highlighted = checkAndGetQuotient(
        balanceParenthesis(returnedText, selectedPart)
      );
      console.log("highlighted 1: " + highlighted);
      setHighlightedText(highlighted);
      onHighlightChange(getStartIndex(highlighted));
      setSelectionRange({
        start: getStartIndex(highlighted),
        end: getEndIndex(highlighted)
      });
    } else {
      const highlighted = checkAndGetQuotient(selectedPart);
      console.log("highlighted 2: " + highlighted);
      setHighlightedText(highlighted);
      onHighlightChange(getStartIndex(highlighted));
      setSelectionRange({
        start: getStartIndex(highlighted),
        end: getEndIndex(highlighted)
      });
    }
  };
*/
const handelHighlight = (selectionRange) => {
  const selectedPart = findSelectionParenthesis(equation, selectionRange);
  if (!checkParenthesisConsistency(selectedPart)) {
    const highlighted = checkAndGetQuotient(
      balanceParenthesis(equation, selectedPart)
    );
    console.log("highlighted 1: " + highlighted);
    setHighlightedText(highlighted);
    onHighlightChange(getStartIndex(highlighted));
    setSelectionRange({
      start: getStartIndex(highlighted),
      end: getEndIndex(highlighted)
    });
  } else {
    const highlighted = checkAndGetQuotient(selectedPart);
    console.log("highlighted 2: " + highlighted);
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
 // replace all instances of returnedText with equation
 /*
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
  */
  const getEndIndex = useCallback(
    (start) => {
      if (equation[start] === "(") {
        let stack = 1;
        for (let i = start + 1; i < equation.length; i++) {
          if (equation[i] === "(") stack++;
          else if (equation[i] === ")") stack--;
          if (stack === 0) return i;
        }
      }
      if (equation[start] === "'") {
        if (equation[start + 1] === "(") {
          let stack = 1;
          for (let i = start + 2; i < equation.length; i++) {
            if (equation[i] === "(") stack++;
            else if (equation[i] === ")") stack--;
            if (stack === 0) return i;
          }
        }
      }
      if (/^[a-zA-Z0-9]+$/.test(equation.substring(start))) {
        return equation.length - 1;
      }
      for (let i = start + 1; i < equation.length; i++) {
        if (!/^[a-zA-Z0-9]$/.test(equation[i])) {
          return i - 1;
        }
      }
      return equation.length - 1;
    },
    [equation]
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
      console.log("start: " + start);
      console.log("end: " + end);
      console.log("replacement: " + replacement);
      return (
        beforeSelection +
        `<span class="highlight">${replacement}</span>` +
        afterSelection
      );
    },
    []
  );
/*
  useEffect(() => {
    console.log(`My index is ${ myIndex }`)
    console.log(`I should do highlight: ${ shouldApplyKeyStroke }`)
    console.log(`I believe the last keystoke was ${ keyStroke }`)
  });
*/
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

useEffect(() => {
  const applyKeyStroke = (e) => {
    //console.log("handle key up executed");
    console.log("current selected = "+ selected);
    //console.log("key pressed: " + e.key);
      let newSelected = selected;
      //console.log("initialized, key = "+ jsonTree_dict[selected]);
      //if (selected === null) {
        // should only happen on first render; might be unnecessary
      //  return;
      //}
      //if (!jsonTree[selected]) {
      //  console.warn("Selected index is out of bounds.");
      //  return;
      //}
      if (e.key === "ArrowUp") {
        newSelected = jsonTree_dict[selected][0];
        selected = newSelected;
        console.log("up pressed");
        console.log("selected: " + selected);
      } 
      else if (e.key === "ArrowDown") {
        newSelected = jsonTree_dict[selected][1];
        selected = newSelected;
        console.log("down pressed")
        console.log("selected: " + selected);
      } 
      else if (e.key === "ArrowLeft") {
        newSelected = jsonTree_dict[selected][2];
        selected = newSelected;
        console.log("left pressed,");
        console.log("selected: " + selected);
      } 
      else if (e.key === "ArrowRight") {
        newSelected = jsonTree_dict[selected][3];
        selected = newSelected;
        console.log("right pressed");
        console.log("selected: " + selected);
      }
      console.log("current index = "+ selected);
      console.log("current key = "+ jsonTree_dict[selected]);
      console.log(`My index is ${ myIndex }`)
      console.log(`I should do highlight: ${ shouldApplyKeyStroke }`)
      console.log(`I believe the last keystoke was ${ keyStroke }`)
      if (shouldApplyKeyStroke) {
        console.log("apply keystroke for index: " + myIndex);
        highlightWordOrNumber();
      }
  };

  document.addEventListener("keyup", applyKeyStroke);
  //document.addEventListener("keyup", handleKeyUp);
  //console.log("event listener added");
}, []);

// Arrow Key Navigation
/*
useEffect(() => {
    const handleKeyUp = (e) => {
    console.log("current index = "+ selected);
    console.log("key pressed: " + e.key);
    let newSelected = selected;
    //console.log("initialized, key = "+ jsonTree_dict[selected]);
    //if (selected === null) {
      // should only happen on first render; might be unnecessary
    //  return;
    //}
    //if (!jsonTree[selected]) {
    //  console.warn("Selected index is out of bounds.");
    //  return;
    //}
    if (e.key === "ArrowUp") {
      // up selects parent expression
      // if no parent, don't change
      newSelected = jsonTree_dict[selected][0];
      //setSelected({ newSelected });
      //setSelected(newSelected);
      selected = newSelected;
      console.log("up pressed");
    } 
    else if (e.key === "ArrowDown") {
      newSelected = jsonTree_dict[selected][1];
      //setSelected({ newSelected });
      //setSelected(newSelected);
      selected = newSelected;
      // down selects first child value/expression
      // if no children, don't change
      //setSelected((curSelected) =>//{
        //jsonTree_dict[curSelected][1]
      //);
      console.log("down pressed")
    } else if (e.key === "ArrowLeft") {
      newSelected = jsonTree_dict[selected][2];
      //setSelected({ newSelected });
      //setSelected(newSelected);
      selected = newSelected;
      console.log("left pressed,");
    } 
    else if (e.key === "ArrowRight") {
      newSelected = jsonTree_dict[selected][3];
      //setSelected({ newSelected });
      //setSelected(newSelected);
      selected = newSelected;
      console.log("right pressed");
    }
    console.log("current index = "+ selected);
    console.log("current key = "+ jsonTree_dict[selected]);
    highlightWordOrNumber();
    //updateHighlight(selected); // think we are setting selected to a subset of jsonTree_dict... maybe update highlight is causing the issue
    //console.log("start: "+ selected);
    //console.log("end: "+ getEndIndex(selected));
  };
  document.addEventListener("keyup", handleKeyUp);
  //document.addEventListener("keyup", () => console.log("key up listener"));
  return () => {
    document.removeEventListener("keyup", handleKeyUp);
  };
}, [highlightWordOrNumber]);
*/
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
