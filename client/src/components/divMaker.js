// DivMaker.js
function getClassNames(e, selected, resultNode, prefix) {
  const prefixClass = prefix ? `line-${prefix}` : null;
  const lineNumber = parseInt(prefix, 10) || 0;
  
  // Collect all applicable highlight classes
  const highlightClasses = [];
  
  // Determine colors based on line number modulo 4
  // Line 0 (mod 4 = 0): target=yellow, result=green
  // Line 1 (mod 4 = 1): target=blue, result=yellow
  // Line 2 (mod 4 = 2): target=red, result=blue
  // Line 3 (mod 4 = 3): target=green, result=red
  const mod4 = lineNumber % 4;
  const colorCycle = ['yellow', 'blue', 'red', 'green'];
  
  const selectedColor = colorCycle[mod4];
  // Result color comes from previous line's target color
  const resultColor = colorCycle[(mod4 + 3) % 4]; // (mod4 - 1 + 4) % 4
  
  // Only show target highlight if selected is defined (not undefined)
  if (selected !== undefined && selected === e.startPosition) {
    highlightClasses.push(`highlight-${selectedColor}`);
  }
  
  if (resultNode !== undefined && resultNode === e.startPosition) {
    highlightClasses.push(`result-highlight-${resultColor}`);
  }
  
  // If no highlights, add no-highlight class
  if (highlightClasses.length === 0) {
    highlightClasses.push("no-highlight");
  }
  
  return ["node", prefixClass, ...highlightClasses].filter(Boolean).join(" ");
}

function recurse(e, selected, resultNode, jsonDict, prefix) {
  if (!e) {
    return <div>&nbsp;</div>;
  }

  const node = Object.create(e);
  node.children = node.children || [];

  const uniqueId = `${prefix}-${node.startPosition}`;

  if (Array.isArray(node.children) && node.children.length > 0) {
    return (
      <div className={getClassNames(node, selected, resultNode, prefix)} id={uniqueId} key={uniqueId}>
        {node.data}{node.children.map((child) => 
          recurse(jsonDict[child], selected, resultNode, jsonDict, prefix)
        )})
      </div>
    );
  }

  return (
    <div className={getClassNames(node, selected, resultNode, prefix)} id={uniqueId} key={uniqueId}>
      &nbsp;{node.data}&nbsp;
    </div>
  );
}

export default function DivMakerComponent({ expr, selected, resultNode, origTree, lineNumber = 0 }) {
  return recurse(expr[0], selected, resultNode, origTree, lineNumber);
}