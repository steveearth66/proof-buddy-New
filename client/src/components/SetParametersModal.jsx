import React, { useState, useEffect } from "react";
import Modal from "react-bootstrap/Modal";
import Button from "react-bootstrap/Button";
import ButtonGroup from "react-bootstrap/ButtonGroup";

const PARAM_ROWS = [
  { key: "support_errors",          label: "Error Messages" },
  { key: "support_current_lhs_rhs", label: "Current LHS/RHS" },
  { key: "support_ih",              label: "Induction Hypothesis" },
  { key: "support_premise",         label: "Premise" },
  { key: "support_rule_set",        label: "Rule Set" },
  { key: "support_value_mapping",   label: "Value Mapping" },
];

const DEFAULT_PARAMS = {
  support_errors: true,
  support_current_lhs_rhs: true,
  support_ih: true,
  support_premise: true,
  support_rule_set: true,
  support_value_mapping: true,
};

export default function SetParametersModal({ show, onHide, params, onSave }) {
  const [local, setLocal] = useState(DEFAULT_PARAMS);

  // Sync local state whenever modal opens or params change
  useEffect(() => {
    if (show) {
      setLocal({ ...DEFAULT_PARAMS, ...params });
    }
  }, [show, params]);

  const allHigh = PARAM_ROWS.every(r => local[r.key] === true);
  const allLow  = PARAM_ROWS.every(r => local[r.key] === false);

  const setAll = (value) => {
    const next = {};
    PARAM_ROWS.forEach(r => { next[r.key] = value; });
    setLocal(next);
  };

  const toggle = (key, value) => {
    setLocal(prev => ({ ...prev, [key]: value }));
  };

  const handleSave = () => {
    onSave(local);
    onHide();
  };

  return (
    <Modal show={show} onHide={onHide} centered>
      <Modal.Header closeButton>
        <Modal.Title>Set Parameters</Modal.Title>
      </Modal.Header>

      <Modal.Body>
        <table style={{ width: "100%", borderCollapse: "separate", borderSpacing: "0 6px" }}>
          <thead>
            <tr>
              <th style={{ paddingBottom: "4px" }}>Parameter</th>
              <th style={{ textAlign: "center", paddingBottom: "4px" }}>Low Support</th>
              <th style={{ textAlign: "center", paddingBottom: "4px" }}>High Support</th>
            </tr>
          </thead>
          <tbody>
            {/* ALL row */}
            <tr style={{ borderBottom: "1px solid #dee2e6" }}>
              <td style={{ paddingBottom: "8px", fontWeight: "600" }}>ALL</td>
              <td style={{ textAlign: "center", paddingBottom: "8px" }}>
                <Button
                  size="sm"
                  variant={allLow ? "primary" : "outline-secondary"}
                  onClick={() => setAll(false)}
                >
                  Low
                </Button>
              </td>
              <td style={{ textAlign: "center", paddingBottom: "8px" }}>
                <Button
                  size="sm"
                  variant={allHigh ? "primary" : "outline-secondary"}
                  onClick={() => setAll(true)}
                >
                  High
                </Button>
              </td>
            </tr>

            {/* Individual rows */}
            {PARAM_ROWS.map(({ key, label }) => (
              <tr key={key}>
                <td style={{ paddingTop: "4px" }}>{label}</td>
                <td style={{ textAlign: "center", paddingTop: "4px" }}>
                  <Button
                    size="sm"
                    variant={local[key] === false ? "primary" : "outline-secondary"}
                    onClick={() => toggle(key, false)}
                  >
                    Low
                  </Button>
                </td>
                <td style={{ textAlign: "center", paddingTop: "4px" }}>
                  <Button
                    size="sm"
                    variant={local[key] === true ? "primary" : "outline-secondary"}
                    onClick={() => toggle(key, true)}
                  >
                    High
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Modal.Body>

      <Modal.Footer>
        <Button variant="secondary" onClick={onHide}>Cancel</Button>
        <Button variant="primary" onClick={handleSave}>Save</Button>
      </Modal.Footer>
    </Modal>
  );
}
