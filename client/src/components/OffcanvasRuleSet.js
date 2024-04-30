import React, { useState } from "react";
import OffCanvas from "react-bootstrap/Offcanvas";
import Table from "react-bootstrap/Table";
import ruleSet from "./RuleSet";
import Form from "react-bootstrap/Form";

/**
 *  OffcanvasRuleSet component that displays at the bottom of the application in the "er-racket" page when the user presses the "View Rule Set" Button.
 * It uses react-bootstrap's components.
 */

const OffcanvasRuleSet = ({ isActive, toggleFunction }) => {
  const [filteredRules, setFilteredRules] = useState(ruleSet());
  /* Present list of Rules for View Rule Set Offcanvas */
  const rules = ruleSet();

  const onSearch = (e) => {
    const searchValue = e.target.value;
    const filteredRules = rules.filter((rule) => {
      return (
        rule.toFrom.toLowerCase().includes(searchValue.toLowerCase()) ||
        rule.fromTo.toLowerCase().includes(searchValue.toLowerCase()) ||
        rule.name.toLowerCase().includes(searchValue.toLowerCase()) ||
        rule.tags.toLowerCase().includes(searchValue.toLowerCase())
      );
    });
    setFilteredRules(filteredRules);
  };

  return (
    <OffCanvas
      className="Offcanvas"
      id="rule-set"
      show={isActive}
      onHide={toggleFunction}
      scroll="true"
      placement="bottom"
    >
      <OffCanvas.Body>
        <Form.Control
          type="text"
          placeholder="Search"
          className="search-input"
          onChange={onSearch}
        />
        <Table striped bordered hover>
          <thead>
            <tr>
              <th>To/From</th>
              <th>From/To</th>
              <th>Name</th>
              <th>Tag</th>
            </tr>
          </thead>
          <tbody>
            {filteredRules.map((rule, index) => (
              <tr key={index}>
                <td>{rule.toFrom}</td>
                <td>{rule.fromTo}</td>
                <td>{rule.name}</td>
                <td>{rule.tags}</td>
              </tr>
            ))}
          </tbody>
        </Table>
      </OffCanvas.Body>
    </OffCanvas>
  );
};

export default OffcanvasRuleSet;
