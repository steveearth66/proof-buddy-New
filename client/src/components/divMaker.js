// DivMaker.js

// Update getClassNames to use the unique ID when checking the selected node:
function getClassNames(e, selected, prefix) {
  const uniqueId = `${prefix}-${e.startPosition}`;
  return ["node", selected === uniqueId ? "highlight" : "no-highlight"].join(" ");
}

/*
 * The recursive function:
 * - Accepts an extra parameter "prefix" (the line number or other unique identifier)
 * - Constructs a unique identifier by prepending the prefix to e.startPosition
 * - Uses that unique id for both the div's id and its React key.
 */
function recurse(e, selected, jsonDict, prefix) {
  if (e === null || e === undefined || e === "") {
    return <div>&nbsp;</div>;
  }

  // Create a new object based on 'e' (we use a spread operator for clarity)
  const node = { ...e };

  // Ensure that 'children' is an array; if not, set it to an empty array
  if (!node.children) {
    node.children = []; 
  }

  // Create a unique identifier by combining the prefix and the node's startPosition
  const uniqueId = `${prefix}-${node.startPosition}`;

  if (Array.isArray(node.children) && node.children.length > 0) {
    return (
      <div className={getClassNames(node, selected, prefix)} id={uniqueId} key={uniqueId}>
        ({node.children.map((child) => 
          recurse(jsonDict[child], selected, jsonDict, prefix)
        )})
      </div>
    );
  } else {
    return (
      <div className={getClassNames(node, selected, prefix)} id={uniqueId} key={uniqueId}>
        &nbsp;{node.data}&nbsp;
      </div>
    );
  }
}

// DivMakerComponent now accepts an extra prop "lineNumber" which is used as the prefix
export default function DivMakerComponent({ expr, selected, origTree, lineNumber = 0 }) {
  // Here we pass "lineNumber" as the prefix to the recursive rendering function.
  return recurse(expr[0], selected, origTree, lineNumber);
}