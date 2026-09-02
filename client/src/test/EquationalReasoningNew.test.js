/**
 * Jest + jsdom UI tests for EquationalReasoningNew.
 * Mirrors the mock-wall pattern in InductionRacket.test.js: mount the real page,
 * stub services/layout/heavy children so tests run without Django or a browser.
 */
import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import EquationalReasoningNew from "../pages/EquationalReasoningNew";

const mockToggleSide = jest.fn();

// --- Service mocks (no live HTTP) ---
jest.mock("react-toastify", () => ({
  toast: {
    error: jest.fn(),
  },
}));

// Start-proof flow also calls inductionService.checkNameConflict before the confirm modal.
// Real Equational page uses inductionService.checkNameConflict.
jest.mock("../services/inductionService", () => ({
  checkNameConflict: jest.fn().mockResolvedValue({ conflict: false }),
}));

// --- Router / layout / modal stubs ---
jest.mock("react-router-dom", () => ({
  useLocation: () => ({ state: null, pathname: "/equational" }),
  useNavigate: () => jest.fn(),
}));

// Lightweight Modal so confirm/overwrite dialogs render in jsdom without Bootstrap JS.
jest.mock("react-bootstrap/Modal", () => {
  const React = require("react");
  const Modal = ({ show, children, onHide }) =>
    show ? React.createElement("div", { role: "dialog", "data-testid": "modal" }, children) : null;
  Modal.Header = ({ children }) => React.createElement("div", null, children);
  Modal.Title = ({ children }) => React.createElement("h5", null, children);
  Modal.Body = ({ children }) => React.createElement("div", null, children);
  Modal.Footer = ({ children }) => React.createElement("div", null, children);
  return { __esModule: true, default: Modal };
});

jest.mock("../layouts/MainLayout", () => {
  const React = require("react");
  return {
    __esModule: true,
    default: function MainLayout({ children }) {
      return React.createElement("div", { "data-testid": "main-layout" }, children);
    },
  };
});

jest.mock("../components/OffcanvasRuleSet", () => {
  const React = require("react");
  return {
    __esModule: true,
    default: function OffcanvasRuleSet({ isActive, toggleFunction }) {
      return React.createElement("div", { "data-testid": "offcanvas-ruleset" }, isActive && "Active");
    },
  };
});


// CommentsModal is not under test here.
jest.mock("../components/CommentsModal", () => {
  const React = require("react");
  return {
    __esModule: true,
    default: function CommentsModal() {
      return null;
    },
  };
});

// Not under test here; equational validation does not depend on support params.
jest.mock("../components/SetParametersModal", () => {
  const React = require("react");
  return {
    __esModule: true,
    default: function SetParametersModal() {
      return null;
    },
  };
});

// Barrel components: simple stubs so the page mounts; RacketInput is a plain input
// (no forwardRef — may log a ref warning; harmless for these tests).
jest.mock("../components", () => {
  const React = require("react");
  return {
    Definitions: function Definitions( toggleDefinitionsWindow ) {
      return React.createElement("div", { "data-testid": "definitions" }, "Definitions Window");
    },
    ProofComplete: function ProofComplete() {
      return React.createElement("div", { "data-testid": "proof-complete" }, "Proof Complete!");
    },
    PersistentPad: function PersistentPad({ equation, onHighlightChange, side }) {
      return React.createElement("div", { "data-testid": `persistent-pad-${side}` }, [
        equation,
        React.createElement("button", { onClick: () => onHighlightChange(0), key: "btn" }, "Highlight"),
      ]);
    },
    Substitution: function Substitution({ show, handleClose }) {
      return show ? React.createElement("div", { "data-testid": "substitution-modal" }, "Substitution Modal") : null;
    },
    RacketInput: function RacketInput({ id, name, value, placeholder, onChange, disabled }) {
      return React.createElement("input", { "data-testid": `racket-input-${name}`, id, name, value: value || "", placeholder: placeholder || "", onChange: onChange || (() => {}), disabled });
    },
  };
});

// --- Hook mocks: keep real useInputState so form typing works; stub the rest ---
jest.mock("../hooks/useToggleSide", () => ({
  useToggleSide: () => {
    const React = require("react");
    const [showSide, setShowSide] = React.useState("LHS");
    const toggle = () => {
      setShowSide((prev) => (prev === "LHS" ? "RHS" : "LHS"));
      mockToggleSide();
    };
    return [showSide, toggle];
  },
}));

jest.mock("../hooks/useOffcanvas", () => ({
  useOffcanvas: () => [false, jest.fn()],
}));

jest.mock("../hooks/useInputState", () => ({
  useInputState: (initialValues) => {
    const React = require("react");
    const [values, setValues] = React.useState(initialValues);
    const handleChange = (e) => {
      const { name, value } = e.target;
      setValues((prev) => ({ ...prev, [name]: value }));
    };
    return [values, handleChange, setValues];
  },
}));

jest.mock("../hooks/useFormValidation", () => ({
  useFormValidation: () => [{}, jest.fn(), jest.fn(), true],
}));

// Equational page uses useGoalCheck (not useInductionCheck). Return shape must match
// the real hook's tuple length so destructuring in the page does not break.
jest.mock("../hooks/useGoalCheck", () => ({
  useGoalCheck: (handleChange) => [
    { LHS: false, RHS: false },
    jest.fn().mockResolvedValue(undefined),
    { LHS: "", RHS: "" },
    handleChange,
    { name: "", tag: "" },
    jest.fn(),
    jest.fn(),
    {},
    jest.fn(),
  ],
}));

// validationErrors must be { LHS: {}, RHS: {} } if proof-started UI ever renders.
jest.mock("../hooks/useRacketRuleFields", () => ({
  useRacketRuleFields: () => [
    { LHS: [], RHS: [] },
    jest.fn(),
    jest.fn(),
    { LHS: {}, RHS: {} },
    null,
    [],
    jest.fn(),
    jest.fn(),
    false,
    jest.fn(),
    jest.fn(),
    [],
    jest.fn(),
    jest.fn(),
  ],
}));

jest.mock("../hooks/useCurrentRacketValues", () => ({
  useCurrentRacketValues: () => ["", ""],
}));

jest.mock("../hooks/useFormSubmit", () => ({
  useFormSubmit: () => ({ handleSubmit: jest.fn((e) => e.preventDefault()) }),
}));

jest.mock("../hooks/useExportToLocalMachine", () => ({
  useExportToLocalMachine: () => jest.fn(),
}));

jest.mock("../hooks/useDefinitionsWindow", () => ({
  useDefinitionsWindow: () => [false, jest.fn()],
}));

describe("EquationalReasoningNew Component", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Fresh mount each test → initializeProofSession logs "No active session" (expected).
    sessionStorage.clear();
  });

  describe("Component Rendering", () => {
    test("renders the page heading", () => {
      render(<EquationalReasoningNew />);
      expect(screen.getAllByText("Equational Reasoning")[0]).toBeInTheDocument();
    });

    test("renders proof name and tag fields", () => {
      render(<EquationalReasoningNew />);
      expect(screen.getByPlaceholderText("Enter name")).toBeInTheDocument();
      expect(screen.getByLabelText("# Tag")).toBeInTheDocument();
    });

    test("renders goal input fields", () => {
      render(<EquationalReasoningNew />);
      expect(screen.getByPlaceholderText("LHS Goal")).toBeInTheDocument();
      expect(screen.getByPlaceholderText("RHS Goal")).toBeInTheDocument();
    });

    test("renders without crashing on mount", () => {
      expect(() => render(<EquationalReasoningNew />)).not.toThrow();
    });
  });

  describe("Button Interactions", () => {
    test("renders Proof Utilities dropdown toggle", () => {
      render(<EquationalReasoningNew />);
      // In jsdom the toggle often shows only the tools icon, not "Proof Utilities" text.
      expect(
        document.getElementById("dropdown-autoclose-true")
      ).toBeInTheDocument();
    });

    test("renders Start Equational Reasoning Proof button before proof is started", () => {
      render(<EquationalReasoningNew />);
      expect(
        screen.getByText("Start Equational Reasoning Proof")
      ).toBeInTheDocument();
    });
  });

  describe("Current State Display", () => {
    test("renders Current LHS and Current RHS labels", () => {
      render(<EquationalReasoningNew />);
      expect(screen.getAllByText("Current LHS").length);
      expect(screen.getAllByText("Current RHS").length);
    });

    test("has at least two read-only text fields for current values", () => {
      render(<EquationalReasoningNew />);
      const readonlyInputs = screen.getAllByRole("textbox").filter((el) => el.readOnly);
      expect(readonlyInputs.length).toBeGreaterThanOrEqual(2);
    });
  });

  describe("Form Input Handling", () => {
    test("updates proof name field when typed into", async () => {
      render(<EquationalReasoningNew />);
      const input = screen.getByPlaceholderText("Enter name");
      userEvent.type(input, "My Proof");
      await waitFor(() => expect(input).toHaveValue("My Proof"));
    });

    test("updates LHS goal field when typed into", async () => {
      render(<EquationalReasoningNew />);
      const input = screen.getByPlaceholderText("LHS Goal");
      userEvent.type(input, "(+ 1 2)");
      await waitFor(() => expect(input).toHaveValue("(+ 1 2)"));
    });

    test("updates RHS goal field when typed into", async () => {
      render(<EquationalReasoningNew />);
      const input = screen.getByPlaceholderText("RHS Goal");
      userEvent.type(input, "3");
      await waitFor(() => expect(input).toHaveValue("3"));
    });

    test("updates only LHS goal field when only LHS goal is typed into", async () => {
      render(<EquationalReasoningNew />);
      const lhs = screen.getByPlaceholderText("LHS Goal");
      const rhs = screen.getByPlaceholderText("RHS Goal");
      userEvent.type(lhs, "(+ 1 2)");
      await waitFor(() => expect(lhs).toHaveValue("(+ 1 2)"));
      expect(rhs).toHaveValue("");
    });

    test("updates only RHS goal field when only RHS goal is typed into", async () => {
      render(<EquationalReasoningNew />);
      const lhs = screen.getByPlaceholderText("LHS Goal");
      const rhs = screen.getByPlaceholderText("RHS Goal");
      userEvent.type(rhs, "3");
      await waitFor(() => expect(rhs).toHaveValue("3"));
      expect(lhs).toHaveValue("");
    });
  });

  describe("Validation Logic", () => {
    // Equational start validation uses setErrors + Alert (not toast like Induction).
    // Errors run in handleStartProof before the confirm modal opens.
    // fireEvent.submit bypasses HTML5 required-field blocking so client-side rules are tested.

    test("shows error when proof name is missing", async () => {
      const { container } = render(<EquationalReasoningNew />);
      userEvent.type(screen.getByPlaceholderText("LHS Goal"), "(+ 1 2)");
      userEvent.type(screen.getByPlaceholderText("RHS Goal"), "3");
      fireEvent.submit(container.querySelector("form"));
      await waitFor(() =>
        expect(screen.getByText("Name is required")).toBeInTheDocument()
      );
    });

    test("shows error when goals are missing", async () => {
      const { container } = render(<EquationalReasoningNew />);
      userEvent.type(screen.getByPlaceholderText("Enter name"), "My Proof");
      fireEvent.submit(container.querySelector("form"));
      await waitFor(() =>
        expect(
          screen.getByText("Both LHS and RHS goals are required")
        ).toBeInTheDocument()
      );
    });

    test("shows error when LHS and RHS goals are identical", async () => {
      const { container } = render(<EquationalReasoningNew />);
      userEvent.type(screen.getByPlaceholderText("Enter name"), "My Proof");
      userEvent.type(screen.getByPlaceholderText("LHS Goal"), "3");
      userEvent.type(screen.getByPlaceholderText("RHS Goal"), "3");
      fireEvent.submit(container.querySelector("form"));
      await waitFor(() =>
        expect(
          screen.getByText("LHS and RHS goals cannot be identical")
        ).toBeInTheDocument()
      );
    });

    test("shows error for reserved proof name", async () => {
      const { container } = render(<EquationalReasoningNew />);
      userEvent.type(screen.getByPlaceholderText("Enter name"), "IH");
      userEvent.type(screen.getByPlaceholderText("LHS Goal"), "(+ 1 2)");
      userEvent.type(screen.getByPlaceholderText("RHS Goal"), "3");
      fireEvent.submit(container.querySelector("form"));
      await waitFor(() =>
        expect(
          screen.getByText(/reserved name/i)
        ).toBeInTheDocument()
      );
    });

    // Stops at the confirm modal; clicking Start Proof would need a fuller equationalService mock.
    test("confirmation modal appears when valid start form is submitted", async () => {
      const { container } = render(<EquationalReasoningNew />);
      userEvent.type(screen.getByPlaceholderText("Enter name"), "My Proof");
      userEvent.type(screen.getByPlaceholderText("LHS Goal"), "(+ 1 2)");
      userEvent.type(screen.getByPlaceholderText("RHS Goal"), "3");
      fireEvent.submit(container.querySelector("form"));
      await waitFor(() =>
        expect(
          screen.getByText(/Do you wish to proceed/i)
        ).toBeInTheDocument()
      );
      expect(screen.getByRole("button", { name: "Start Proof" })).toBeInTheDocument();
    });
  });
});
