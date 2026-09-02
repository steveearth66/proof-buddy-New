import React from "react";
import { render, screen, fireEvent, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { toast } from "react-toastify";
import InductionRacket from "../pages/InductionRacket";
import inductionService from "../services/inductionService";

// When true, force the real SetParametersModal open (RB Dropdown menus often
// do not stay open under jsdom). Reset in beforeEach so other tests are unaffected.
// Name must start with `mock` so jest.mock factory can close over it.
let mockForceShowSetParametersModal = false;

jest.mock("react-toastify", () => ({
  toast: {
    error: jest.fn(),
  },
}));

jest.mock("../services/inductionService", () => ({
  checkNameConflict: jest.fn().mockResolvedValue({ conflict: false }),
}));

// wraps real SetParametersModal in a mock that forces it to open when mockForceShowSetParametersModal is true
jest.mock("../components/SetParametersModal", () => {
  const React = require("react");
  const Actual = jest.requireActual("../components/SetParametersModal").default;
  return {
    __esModule: true,
    default: function SetParametersModal(props) {
      return React.createElement(Actual, {
        ...props,
        show: mockForceShowSetParametersModal || props.show,
      });
    },
  };
});

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

// (no forwardRef — may log a ref warning; harmless for these tests).
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
    return [values, handleChange, setValues];
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
    mockForceShowSetParametersModal = false;
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

    test("updates LHS goal field when typed into", async () => {
      render(<InductionRacket />);
      const input = screen.getByPlaceholderText("LHS Goal");
      userEvent.type(input, "(f n)");
      await waitFor(() => expect(input).toHaveValue("(f n)"));
    });

    test("updates RHS goal field when typed into", async () => {
      render(<InductionRacket />);
      const input = screen.getByPlaceholderText("RHS Goal");
      userEvent.type(input, "(f n)");
      await waitFor(() => expect(input).toHaveValue("(f n)"));
    });

    test("updates only LHS goal field when only LHS goal is typed into", async () => {
      render(<InductionRacket />);
      const lhs = screen.getByPlaceholderText("LHS Goal");
      const rhs = screen.getByPlaceholderText("RHS Goal");
      userEvent.type(lhs, "(f n)");
      await waitFor(() => expect(lhs).toHaveValue("(f n)"));
      expect(rhs).toHaveValue("");
    });

    test("updates only RHS goal field when only RHS goal is typed into", async () => {
      render(<InductionRacket />);
      const lhs = screen.getByPlaceholderText("LHS Goal");
      const rhs = screen.getByPlaceholderText("RHS Goal");
      userEvent.type(rhs, "(f n)");
      await waitFor(() => expect(rhs).toHaveValue("(f n)"));
      expect(lhs).toHaveValue("");
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

    test("shows error when inductive hypothesis is missing when ih support is false", async () => {
      mockForceShowSetParametersModal = true;
      const { container } = render(<InductionRacket />);

      // Real SetParametersModal (forced open: jsdom often fails to open RB Dropdown menus)
      await waitFor(() => screen.getByText("Induction Hypothesis"));
      const ihRow = screen.getByText("Induction Hypothesis").closest("tr");
      // fireEvent: OverlayTrigger-wrapped buttons often miss userEvent clicks in jsdom
      fireEvent.click(within(ihRow).getByRole("button", { name: "Low" }));
      // Clear flag before Save so the re-render from onSave/onHide actually closes the modal
      mockForceShowSetParametersModal = false;
      fireEvent.click(screen.getByRole("button", { name: "Save" }));

      await waitFor(() =>
        expect(screen.getByPlaceholderText("Enter Inductive Hypothesis LHS")).toBeInTheDocument()
      );

      // All checks before IH pass: valid anchor, non-overlapping leap var; IH left empty
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

    test("confirmation modal closes when Cancel is clicked", async () => {
      const { container } = render(<InductionRacket />);
      fireEvent.submit(container.querySelector("form"));
      await waitFor(() =>
        expect(screen.getByText("Are you sure you want to continue?")).toBeInTheDocument()
      );
      userEvent.click(screen.getByRole("button", { name: "Cancel" }));
      await waitFor(() =>
        expect(screen.queryByText("Are you sure you want to continue?")).not.toBeInTheDocument()
      );
      expect(screen.getByText("Start Induction Proof")).toBeInTheDocument();
    });
  });
});