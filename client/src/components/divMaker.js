import { useEffect, useRef } from 'react';
import ID2NODE from "./PersistentPad"; // Steve's addition based on Galen's idea

function enrich(expr) {
  if (expr === null || expr === undefined || expr === "") {
    return;
  }
  expr.parent = null;
  expr.leftSib = null;
  expr.rightSib = null;

  let queue = [expr];
  let id = 0;
  let e;

  while (queue.length > 0) {
    e = queue.shift();
    e.id = id++;

    for (let i = 0; i < e.children.length; i++) {
      let child = e.children[i];
      child.parent = e.id;

      if (i === 0) {
        child.leftSib = null;
      } else {
        child.leftSib = e.children[i - 1].id;
      }
      if (i === e.children.length - 1) {
        child.rightSib = null;
      } else {
        child.rightSib = e.children[i + 1].id;
      }

      queue.push(child);
    }
  }
}

function subChildIDS(expr) {
  if (expr === null || expr === undefined || expr === "") {
    return;
  }
  for (let i = 0; i < expr.children.length; i++) {
    let child = expr.children[i];
    expr.children[i] = child.id;
    subChildIDS(child);
  }
}

function getClassNames(e, selected) {
  return ["node", selected.id === e.id ? "highlight" : "no-highlight"].join(" ");
}
/*
function recurse(e, selected) {
  if (e === null || e === undefined || e === "") {
    return <div>&nbsp;</div>;
  }

  // Check if e has children and if children is an array
  if (!e.children) {
    e.children = []; // Set to empty array if it's not defined
  }

  if (Array.isArray(e.children) && e.children.length > 0) {
    return (
      <div className={getClassNames(e, selected)} id={e.id} key={e.id}>
        ({e.children.map((child) => recurse(ID2NODE(child), false))})
      </div>
    );
  } else {
    return (
      <div className={getClassNames(e, selected)} id={e.id} key={e.id}> 
        &nbsp;{e.data}&nbsp;
      </div>
    );
  }
}
  */
function recurse(e, selected) {
  if (e === null || e === undefined || e === "") {
    return <div>&nbsp;</div>;
  }

  // Create a new object based on 'e' to avoid modifying the original object
  const node = Object.create(e);

  // Ensure that 'children' is an array (if it's missing or not defined)
  if (!node.children) {
    node.children = []; // Set it to an empty array if it's undefined
  }

  if (Array.isArray(node.children) && node.children.length > 0) {
    return (
      <div className={getClassNames(node, selected)} id={node.id} key={node.id}>
        ({node.children.map((child) => recurse(ID2NODE(child), false))})
      </div>
    );
  } else {
    return (
      <div className={getClassNames(node, selected)} id={node.id} key={node.id}>
        &nbsp;{node.data}&nbsp;
      </div>
    );
  }
}

export default function DivMakerComponent({ expr, selected, origTree }) {
  const prevOrigTree = useRef();

  useEffect(() => {
    if (prevOrigTree.current !== origTree) {
      enrich(expr, origTree); // Only call enrich if origTree has changed
      subChildIDS(expr, origTree); // Process the tree if origTree changes
      prevOrigTree.current = origTree; // Update prevOrigTree to the new origTree
    }
  }, [origTree, expr]); // Run this effect when origTree or expr changes

  console.log(expr);  // Log expr after modifications

  return recurse(expr, selected);  // Return the result of the recurse function
}