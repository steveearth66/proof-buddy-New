import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { toast } from "react-toastify";
import InductionRacket from "../pages/InductionRacket";
import inductionService from "../services/inductionService";

jest.mock("react-toastify", () => ({
  toast: {
    error: jest.fn(),
  },
}));

jest.mock("../services/inductionService", () => ({
  checkNameConflict: jest.fn().mockResolvedValue({ conflict: false }),
}));

jest.mock("react-router-dom", () => ({
  useLocation: () => ({ state: null, pathname: '/induction' }),
  useNavigate: () => jest.fn(),
}));

jest.mock("react-bootstrap/Modal", () => {
  const React = require('react');
  const Modal = ({ show, children, onHide }) =>
    show ? React.createElement('div', { role: 'dialog', 'data-testid': 'modal' }, children) : null;
  Modal.Header = ({ children }) => React.createElement('div', null, children);
  Modal.Title = ({ children }) => React.createElement('h5', null, children);
  Modal.Body = ({ children }) => React.createElement('div', null, children);
  Modal.Footer = ({ children }) => React.createElement('div', null, children);
  return { __esModule: true, default: Modal };
});

jest.mock("../layouts/MainLayout", () => {
  const React = require('react');
  return {
    __esModule: true,
    default: function MainLayout({ children }) {
      return React.createElement('div', { 'data-testid': 'main-layout' }, children);
    }
  };
});

jest.mock("../components/OffcanvasRuleSet", () => {
  const React = require('react');
  return {
    __esModule: true,
    default: function OffcanvasRuleSet({ isActive, toggleFunction }) {
      return React.createElement('div', { 'data-testid': 'offcanvas-ruleset' }, isActive && "Active");
    }
  };
});

jest.mock("../components", () => {
  const React = require('react');
  return {
    Definitions: function Definitions({ toggleDefinitionsWindow }) {
      return React.createElement('div', { 'data-testid': 'definitions' }, 'Definitions Window');
    },
    ProofComplete: function ProofComplete() {
      return React.createElement('div', { 'data-testid': 'proof-complete' }, 'Proof Complete!');
    },
    PersistentPad: function PersistentPad({ equation, onHighlightChange, side }) {
      return React.createElement('div', { 'data-testid': `persistent-pad-${side}` }, [
        equation,
        React.createElement('button', { onClick: () => onHighlightChange(0), key: 'btn' }, 'Highlight')
      ]);
    },
    Substitution: function Substitution({ show, handleClose }) {
      return show ? React.createElement('div', { 'data-testid': 'substitution-modal' }, 'Substitution Modal') : null;
    },
    RacketInput: function RacketInput({ id, name, value, placeholder, onChange, disabled }) {
      return React.createElement('input', { 'data-testid': `racket-input-${name}`, id, name, value: value || '', placeholder: placeholder || '', onChange: onChange || (() => {}), disabled });
    },
  };
});

jest.mock("../hooks/useToggleSide", () => ({
  useToggleSide: () => {
    const React = require('react');
    const [showSide, setShowSide] = React.useState('LHS');
    const toggle = () => {
      setShowSide(prev => prev === 'LHS' ? 'RHS' : 'LHS');
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
    const React = require('react');
    const [values, setValues] = React.useState(initialValues);
    const handleChange = (e) => {
      const { name, value } = e.target;
      setValues((prev) => ({ ...prev, [name]: value }));
    };
    return [values, handleChange];
  },
}));

jest.mock("../hooks/useFormValidation", () => ({
  useFormValidation: () => [{}, jest.fn(), jest.fn(), true],
}));

jest.mock("../hooks/useInductionCheck", () => ({
  __esModule: true,
  default: (handleChange) => ({
    isGoalChecked: { LHS: {}, RHS: {} },
    checkGoal: jest.fn(),
    goalValidationMessage: { LHS: {}, RHS: {} },
    enhancedHandleChange: handleChange,
    proofValidationMessage: {},
    clearProofValidationMessage: jest.fn(),
    clearGoalValidationMessage: jest.fn(),
  }),
}));

jest.mock("../hooks/useRacketRuleFields", () => ({
  useRacketRuleFields: () => [
    { LHS: [], RHS: [] },
    jest.fn(),
    jest.fn(),
    { LHS: [], RHS: [] },
    null,
    [],
    jest.fn(),
    jest.fn(),
    false,
    jest.fn(),
    jest.fn(),
    [],
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

describe("InductionRacket Component", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    sessionStorage.clear();
  });

  // Helper: submit the form via fireEvent to bypass HTML5 constraint validation,
  // then wait for and confirm the Start Proof confirmation modal.
  async function submitAndConfirm(container) {
    fireEvent.submit(container.querySelector("form"));
    await waitFor(() => screen.getByRole("button", { name: "Start Proof" }));
    userEvent.click(screen.getByRole("button", { name: "Start Proof" }));
  }

  describe("Component Rendering", () => {
    test("renders the page heading", () => {
      render(<InductionRacket />);
      expect(screen.getAllByText("Induction: Racket")[0]).toBeInTheDocument();
    });

    test("renders proof name and tag fields", () => {
      render(<InductionRacket />);
      expect(screen.getByPlaceholderText("Enter name")).toBeInTheDocument();
      expect(screen.getByLabelText("# Tag")).toBeInTheDocument();
    });

    test("renders induction parameter fields", () => {
      render(<InductionRacket />);
      expect(screen.getByPlaceholderText("Induction Variable")).toBeInTheDocument();
      expect(screen.getByPlaceholderText("Anchor Value")).toBeInTheDocument();
      expect(screen.getByPlaceholderText("Leap Variable")).toBeInTheDocument();
    });

    test("renders goal input fields", () => {
      render(<InductionRacket />);
      expect(screen.getByPlaceholderText("LHS Goal")).toBeInTheDocument();
      expect(screen.getByPlaceholderText("RHS Goal")).toBeInTheDocument();
    });

    test("renders without crashing on mount", () => {
      expect(() => render(<InductionRacket />)).not.toThrow();
    });
  });

  describe("Induction Type Radio Buttons", () => {
    test("renders Integers and Lists radio buttons", () => {
      render(<InductionRacket />);
      expect(screen.getByLabelText("Integers")).toBeInTheDocument();
      expect(screen.getByLabelText("Lists")).toBeInTheDocument();
    });

    test("Integers radio is checked by default", () => {
      render(<InductionRacket />);
      expect(screen.getByLabelText("Integers")).toBeChecked();
    });
  });

  describe("Button Interactions", () => {
    test("renders Proof Utilities dropdown", () => {
      render(<InductionRacket />);
      expect(screen.getByText("Proof Utilities")).toBeInTheDocument();
    });

    test("renders Start Induction Proof button before proof is started", () => {
      render(<InductionRacket />);
      expect(screen.getByText("Start Induction Proof")).toBeInTheDocument();
    });
  });

  describe("Current State Display", () => {
    test("renders Current LHS and Current RHS labels", () => {
      render(<InductionRacket />);
      expect(screen.getByText("Current LHS")).toBeInTheDocument();
      expect(screen.getByText("Current RHS")).toBeInTheDocument();
    });

    test("has at least two read-only text fields for current values", () => {
      render(<InductionRacket />);
      const readonlyInputs = screen.getAllByRole("textbox").filter((el) => el.readOnly);
      expect(readonlyInputs.length).toBeGreaterThanOrEqual(2);
    });
  });

  describe("Form Input Handling", () => {
    test("updates proof name field when typed into", async () => {
      render(<InductionRacket />);
      const input = screen.getByPlaceholderText("Enter name");
      userEvent.type(input, "My Proof");
      await waitFor(() => expect(input).toHaveValue("My Proof"));
    });

    test("updates induction variable field when typed into", async () => {
      render(<InductionRacket />);
      const input = screen.getByPlaceholderText("Induction Variable");
      userEvent.type(input, "n");
      await waitFor(() => expect(input).toHaveValue("n"));
    });

    test("updates anchor value field when typed into", async () => {
      render(<InductionRacket />);
      const input = screen.getByPlaceholderText("Anchor Value");
      userEvent.type(input, "0");
      await waitFor(() => expect(input).toHaveValue("0"));
    });

    test("updates leap variable field when typed into", async () => {
      render(<InductionRacket />);
      const input = screen.getByPlaceholderText("Leap Variable");
      userEvent.type(input, "k");
      await waitFor(() => expect(input).toHaveValue("k"));
    });
  });

  describe("Validation Logic", () => {
    test("shows error when anchor value is not an integer", async () => {
      const { container } = render(<InductionRacket />);
      userEvent.type(screen.getByPlaceholderText("Induction Variable"), "n");
      userEvent.type(screen.getByPlaceholderText("Anchor Value"), "abc");
      userEvent.type(screen.getByPlaceholderText("Leap Variable"), "k");
      await submitAndConfirm(container);
      await waitFor(() =>
        expect(toast.error).toHaveBeenCalledWith("Anchor value must be a nonnegative integer.")
      );
    });

    test("shows error when anchor value is negative", async () => {
      const { container } = render(<InductionRacket />);
      userEvent.type(screen.getByPlaceholderText("Induction Variable"), "n");
      userEvent.type(screen.getByPlaceholderText("Anchor Value"), "-1");
      userEvent.type(screen.getByPlaceholderText("Leap Variable"), "k");
      await submitAndConfirm(container);
      await waitFor(() =>
        expect(toast.error).toHaveBeenCalledWith("Anchor value must be a nonnegative integer.")
      );
    });

    test("shows error when leap variable equals induction variable", async () => {
      const { container } = render(<InductionRacket />);
      userEvent.type(screen.getByPlaceholderText("Induction Variable"), "n");
      userEvent.type(screen.getByPlaceholderText("Anchor Value"), "0");
      userEvent.type(screen.getByPlaceholderText("Leap Variable"), "n");
      userEvent.type(screen.getByPlaceholderText("LHS Goal"), "(f n)");
      await submitAndConfirm(container);
      await waitFor(() =>
        expect(toast.error).toHaveBeenCalledWith("Leap variable must not overlap with variables in the goal.")
      );
    });

    test("shows error when leap variable appears in goal expression", async () => {
      const { container } = render(<InductionRacket />);
      userEvent.type(screen.getByPlaceholderText("Induction Variable"), "n");
      userEvent.type(screen.getByPlaceholderText("Anchor Value"), "0");
      userEvent.type(screen.getByPlaceholderText("Leap Variable"), "k");
      userEvent.type(screen.getByPlaceholderText("LHS Goal"), "(f n k)");
      await submitAndConfirm(container);
      await waitFor(() =>
        expect(toast.error).toHaveBeenCalledWith("Leap variable must not overlap with variables in the goal.")
      );
    });

    test("shows error when inductive hypothesis is missing", async () => {
      const { container } = render(<InductionRacket />);
      // All checks before IH pass: valid anchor, non-overlapping leap var
      userEvent.type(screen.getByPlaceholderText("Induction Variable"), "n");
      userEvent.type(screen.getByPlaceholderText("Anchor Value"), "0");
      userEvent.type(screen.getByPlaceholderText("Leap Variable"), "k");
      userEvent.type(screen.getByPlaceholderText("LHS Goal"), "(f n)");
      await submitAndConfirm(container);
      await waitFor(() =>
        expect(toast.error).toHaveBeenCalledWith(
          expect.stringContaining("Inductive hypothesis")
        )
      );
    });

    test("shows error for reserved proof name", async () => {
      const { container } = render(<InductionRacket />);
      userEvent.type(screen.getByPlaceholderText("Enter name"), "IH");
      userEvent.type(screen.getByPlaceholderText("Anchor Value"), "0");
      await submitAndConfirm(container);
      await waitFor(() =>
        expect(toast.error).toHaveBeenCalledWith(
          expect.stringContaining("reserved name")
        )
      );
    });

    test("confirmation modal appears when Start Induction Proof is clicked", async () => {
      const { container } = render(<InductionRacket />);
      fireEvent.submit(container.querySelector("form"));
      await waitFor(() =>
        expect(screen.getByText("Are you sure you want to continue?")).toBeInTheDocument()
      );
    });
  });
});