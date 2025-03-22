function getClassNames(e, selected) {
  return ["node", selected === e.startPosition ? "highlight" : "no-highlight"].join(" ");
}

// this function has been rewritten without ID2NODE. 
// e is the current node, jsonDict is the dictionary of the tree
// selected is the selected node, but eventually everything should be rewritten to just use the node IDs
function recurse(e, selected, jsonDict) {
  if (e === null || e === undefined || e === "") {
    return <div>&nbsp;</div>;
  }

  // Create a new object based on 'e' to avoid modifying the original object.  not sure why Galen did this.
  const node = Object.create(e);

  // Ensure that 'children' is an array (if it's missing or not defined)
  if (!node.children) {
    node.children = []; // Set it to an empty array if it's undefined
  }

  if (Array.isArray(node.children) && node.children.length > 0) {
    return (
      <div className={getClassNames(node, selected)} id={node.startPosition} key={node.startPosition}>
        ({node.children.map((child) => recurse(jsonDict[child], selected, jsonDict))})
      </div>
    );
  } else {
    return (
      <div className={getClassNames(node, selected)} id={node.startPosition} key={node.startPosition}>
        &nbsp;{node.data}&nbsp;
      </div>
    );
  }
}
// expr is the json dictionary, selected is the selected node, and origTree is the original tree
export default function DivMakerComponent({ expr, selected, origTree }) {
  return recurse(expr[0], selected, origTree);  // Return the result of the recurse function
}