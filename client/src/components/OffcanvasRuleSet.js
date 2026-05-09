import React, { useState, useCallback, useEffect, useMemo } from "react";
import OffCanvas from "react-bootstrap/Offcanvas";
import Table from "react-bootstrap/Table";
import ruleSet from "./RuleSet";
import Form from "react-bootstrap/Form";

/**
 * OffcanvasRuleSet component that displays at the bottom of the application in the "er-racket" page when the user presses the "View Rule Set" Button.
 * It uses react-bootstrap's components.
 */
const OffcanvasRuleSet = ({ isActive, toggleFunction, visibleRules = {}, supportRuleSet = false }) => {
  const [searchTerm, setSearchTerm] = useState("");
  const [height, setHeight] = useState(window.innerHeight * 0.3);
  const [isResizing, setIsResizing] = useState(false);

  // Dynamically calculate the rules based on visibility parameters AND search terms
  const [evalRules, applyRules] = useMemo(() => {
    const [allEval, allRewrite] = ruleSet();

    if (supportRuleSet === false) {
      return [allEval, allRewrite];
    }
    
    // 1. Check if the database value represents "empty / all selected"
    let isEmpty = false;
    if (!visibleRules) {
      isEmpty = true;
    } else if (Array.isArray(visibleRules)) {
      isEmpty = visibleRules.length === 0;
    } else if (typeof visibleRules === 'object') {
      isEmpty = Object.keys(visibleRules).length === 0;
    }

    // 2. Filter by instructor visibility
    let allowedEval = allEval;
    let allowedRewrite = allRewrite;

    if (!isEmpty) {
      const evalKeys = visibleRules.eval || [];
      const rewriteKeys = visibleRules.rewrite || [];
      
      allowedEval = allEval.filter(r => evalKeys.includes(r.procedure));
      allowedRewrite = allRewrite.filter(r => rewriteKeys.includes(r.procedure));
    }

    // 3. Filter by user search term
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      const searchFilter = (rule) => {
        return (
          (rule.name ? rule.name.toLowerCase().includes(term) : false) ||
          String(rule.procedure).toLowerCase().includes(term) ||
          String(rule.highlight).toLowerCase().includes(term) ||
          String(rule.result).toLowerCase().includes(term)
        );
      };
      
      return [allowedEval.filter(searchFilter), allowedRewrite.filter(searchFilter)];
    }

    return [allowedEval, allowedRewrite];
  }, [visibleRules, searchTerm]);

  const startResizing = useCallback((e) => {
    e.preventDefault();
    setIsResizing(true);
  }, []);

  const stopResizing = useCallback(() => {
    setIsResizing(false);
  }, []);

  const resize = useCallback(
    (e) => {
      if (isResizing) {
        // Calculate height: Viewport height minus the current mouse Y position
        const newHeight = window.innerHeight - e.clientY;
        
        // Constraints: Min 150px, Max 90% of screen (do not increase to 100% or user will be unable to close)
        if (newHeight > 150 && newHeight < window.innerHeight * 0.9) {
          setHeight(newHeight);
        }
      }
    },
    [isResizing]
  );

  useEffect(() => {
    if (isResizing) {
      window.addEventListener("mousemove", resize);
      window.addEventListener("mouseup", stopResizing);
    } else {
      window.removeEventListener("mousemove", resize);
      window.removeEventListener("mouseup", stopResizing);
    }
    return () => {
      window.removeEventListener("mousemove", resize);
      window.removeEventListener("mouseup", stopResizing);
    };
  }, [isResizing, resize, stopResizing]);

  const onSearch = (e) => {
    setSearchTerm(e.target.value);
  };

  return (
    <OffCanvas
      className="Offcanvas"
      id="rule-set"
      show={isActive}
      onHide={toggleFunction}
      scroll="true"
      placement="bottom"
      style={{ 
        height: `${height}px`, 
        transition: isResizing ? "none" : "transform 0.3s ease-in-out" 
      }}
    >
      <div
        onMouseDown={startResizing}
        style={{
          height: "10px",
          cursor: "ns-resize",
          width: "100%",
          position: "absolute",
          top: 0,
          left: 0,
          zIndex: 1051,
          backgroundColor: isResizing ? "rgba(0,123,255,0.2)" : "transparent"
        }}
      />
      <OffCanvas.Body>
        <Form.Control
          type="text"
          placeholder="Search"
          className="search-input"
          onChange={onSearch}
        />
        <p>
          <strong>Rules must be in the form "<em>&lt;prefix&gt; &lt;name&gt;</em>",
            where <em>&lt;prefix&gt;</em> is the appropriate prefix ("eval", "rewrite", or "apply")
          and <em>&lt;name&gt;</em> is the rule name of the procedure.</strong><br />
          <strong>Examples:</strong> "eval +", "rewrite first-cons", "apply F" (where F is a definition)
        </p>
        <p>Note: any rule can be done in “reverse” (i.e. selecting result to get the highlight) by using the “Substitution” button</p>
        {evalRules.length > 0 && (
          <>
          <h3>"Eval" Procedures:</h3>
        
          <Table striped bordered hover>
            <thead>
              <tr>
                <th>Name/Procedure</th>
                <th>Highlight</th>
                <th>Result</th>
              </tr>
            </thead>
            <tbody>
              {evalRules.map((rule, index) => (
                <tr key={index}>
                  <td>{rule.procedure}</td>
                  <td>{rule.highlight}</td>
                  <td>{rule.result}</td>
                </tr>
              ))}
            </tbody>
          </Table>
          </>
        )}
        {applyRules.length > 0 && (
          <>
            <h3>Rewrite Rules:</h3>
          
            <Table striped bordered hover>
              <thead>
                <tr>
                  <th style={{ width: "10%" }}>Rule Name</th>
                  <th>Highlight</th>
                  <th>Result</th>
                </tr>
              </thead>
              <tbody>
                {applyRules.map((rule, index) => (
                  <tr key={index}>
                    <td>{rule.procedure}</td>
                    <td>{rule.highlight}</td>
                    <td>{rule.result}</td>
                  </tr>
                ))}
              </tbody>
            </Table>
          </>
        )}
      </OffCanvas.Body>
    </OffCanvas>
  );
};

export default OffcanvasRuleSet;
