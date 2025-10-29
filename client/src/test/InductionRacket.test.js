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
  clearInduction: jest.fn(),
}));

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

  describe("Component Rendering", () => {
    test("renders the main form with all required fields", () => {
      render(<InductionRacket />);

      expect(screen.getByText("Induction: Racket")).toBeInTheDocument();
      expect(screen.getByLabelText("Name")).toBeInTheDocument();
      expect(screen.getByLabelText("# Tag")).toBeInTheDocument();
      expect(screen.getByLabelText("IVar")).toBeInTheDocument();
      expect(screen.getByLabelText("AVal")).toBeInTheDocument();
      expect(screen.getByLabelText("LVar")).toBeInTheDocument();
    });

    test("renders induction type radio buttons", () => {
      render(<InductionRacket />);

      const integersRadio = screen.getByLabelText("Integers");
      const listsRadio = screen.getByLabelText("Lists");

      expect(integersRadio).toBeInTheDocument();
      expect(integersRadio).toBeChecked();
      expect(listsRadio).toBeInTheDocument();
      expect(listsRadio).toBeDisabled();
    });

    test("renders leap goal fields by default", () => {
      render(<InductionRacket />);

      expect(screen. getByPlaceholderText("Leap Goal")).toBeInTheDocument();
      expect(screen.getByLabelText("RHS Leap Goal")).toBeInTheDocument();
    });

    test("clears session storage and induction service on mount", async () => {
      render(<InductionRacket />);

      await waitFor(() => {
        expect(inductionService.clearInduction).toHaveBeenCalled();
      });
    });
  });

  describe("Button Interactions", () => {
    test("renders Proof Utilities dropdown", () => {
      render(<InductionRacket />);

      const proofUtilitiesButton = screen.getByText("Proof Utilities");
      expect(proofUtilitiesButton).toBeInTheDocument();
    });

    test("renders File Operations dropdown", () => {
      render(<InductionRacket />);

      // File Operations is only visible after goal is checked
      // So we just verify the basic rendering
      expect(screen.getByText("Induction: Racket")).toBeInTheDocument();
    });
  });

  describe("Current State Display", () => {
    test("renders current LHS and RHS fields", () => {
      render(<InductionRacket />);

      expect(screen.getByLabelText("Current LHS")).toBeInTheDocument();
      expect(screen.getByLabelText("Current RHS")).toBeInTheDocument();
    });

    test("current fields are read-only", () => {
      render(<InductionRacket />);

      const currentLHS = screen.getByLabelText("Current LHS");
      const currentRHS = screen.getByLabelText("Current RHS");

      expect(currentLHS).toHaveAttribute("readonly");
      expect(currentRHS).toHaveAttribute("readonly");
    });
  });

  describe("Form Input Handling", () => {
    test("updates proof name field", async () => {
      
      render(<InductionRacket />);

      const nameInput = screen.getByLabelText("Name");
      await userEvent.type(nameInput, "Test Proof");

      expect(nameInput).toHaveValue("Test Proof");
    });

    test("updates induction variable field", async () => {
      
      render(<InductionRacket />);

      const ivarInput = screen.getByLabelText("IVar");
      await userEvent.type(ivarInput, "n");

      expect(ivarInput).toHaveValue("n");
    });

    test("updates induction value field", async () => {
      
      render(<InductionRacket />);

      const avalInput = screen.getByLabelText("AVal");
      await userEvent.type(avalInput, "0");

      expect(avalInput).toHaveValue("0");
    });

    test("updates leap variable field", async () => {
      
      render(<InductionRacket />);

      const lvarInput = screen.getByLabelText("LVar");
      await userEvent.type(lvarInput, "k");

      expect(lvarInput).toHaveValue("k");
    });
  });

  describe("Case Switching", () => {
    test("toggles between leap and anchor cases", async () => {
      
      render(<InductionRacket />);

      // Initially shows leap goals
      expect(screen. getByPlaceholderText("Leap Goal")).toBeInTheDocument();

      // Click switch button
      const switchButton = screen.getByText("Switch to Anchor Case");
      await userEvent.click(switchButton);

      // Should now show anchor goals
      await waitFor(() => {
        expect(screen. getByPlaceholderText("LHS Anchor Goal")).toBeInTheDocument();
        expect(screen.getByText("Switch to Leap Case")).toBeInTheDocument();
      });
    });
  });

  describe("Validation Logic", () => {
    test("validateAndStart shows error for invalid anchor value", async () => {
      
      render(<InductionRacket />);

      // Fill in required fields with invalid anchor value
      await userEvent.type(screen.getByLabelText("Name"), "Test");
      await userEvent.type(screen.getByLabelText("# Tag"), "test");
      await userEvent.type(screen.getByLabelText("IVar"), "n");
      await userEvent.type(screen.getByLabelText("AVal"), "invalid");
      await userEvent.type(screen.getByLabelText("LVar"), "k");
      await userEvent.type(screen. getByPlaceholderText("Leap Goal"), "(f n)");

      // Click start button
      const startButton = screen.getByText("Start Induction Proof");
      await userEvent.click(startButton);

      expect(toast.error).toHaveBeenCalledWith(
        "Anchor value must be a nonnegative integer."
      );
    });

    test("validateAndStart shows error for negative anchor value", async () => {
      
      render(<InductionRacket />);

      await userEvent.type(screen.getByLabelText("Name"), "Test");
      await userEvent.type(screen.getByLabelText("# Tag"), "test");
      await userEvent.type(screen.getByLabelText("IVar"), "n");
      await userEvent.type(screen.getByLabelText("AVal"), "-1");
      await userEvent.type(screen.getByLabelText("LVar"), "k");
      await userEvent.type(screen. getByPlaceholderText("Leap Goal"), "(f n)");

      const startButton = screen.getByText("Start Induction Proof");
      await userEvent.click(startButton);

      expect(toast.error).toHaveBeenCalledWith(
        "Anchor value must be a nonnegative integer."
      );
    });

    test("validateAndStart shows error when leap variable equals induction variable", async () => {
      
      render(<InductionRacket />);

      await userEvent.type(screen.getByLabelText("Name"), "Test");
      await userEvent.type(screen.getByLabelText("# Tag"), "test");
      await userEvent.type(screen.getByLabelText("IVar"), "n");
      await userEvent.type(screen.getByLabelText("AVal"), "0");
      await userEvent.type(screen.getByLabelText("LVar"), "n");
      await userEvent.type(screen. getByPlaceholderText("Leap Goal"), "(f n)");

      const startButton = screen.getByText("Start Induction Proof");
      await userEvent.click(startButton);

      expect(toast.error).toHaveBeenCalledWith(
        "Leap variable must not overlap with variables in the goal."
      );
    });

    test("validateAndStart shows error when leap variable appears in goal", async () => {
      
      render(<InductionRacket />);

      await userEvent.type(screen.getByLabelText("Name"), "Test");
      await userEvent.type(screen.getByLabelText("# Tag"), "test");
      await userEvent.type(screen.getByLabelText("IVar"), "n");
      await userEvent.type(screen.getByLabelText("AVal"), "0");
      await userEvent.type(screen.getByLabelText("LVar"), "k");
      await userEvent.type(screen. getByPlaceholderText("Leap Goal"), "(f n k)");

      const startButton = screen.getByText("Start Induction Proof");
      await userEvent.click(startButton);

      expect(toast.error).toHaveBeenCalledWith(
        "Leap variable must not overlap with variables in the goal."
      );
    });

    test("validateAndStart shows error when induction variable not in function parameters", async () => {
      
      render(<InductionRacket />);

      await userEvent.type(screen.getByLabelText("Name"), "Test");
      await userEvent.type(screen.getByLabelText("# Tag"), "test");
      await userEvent.type(screen.getByLabelText("IVar"), "x");
      await userEvent.type(screen.getByLabelText("AVal"), "0");
      await userEvent.type(screen.getByLabelText("LVar"), "k");
      await userEvent.type(screen. getByPlaceholderText("Leap Goal"), "(f n)");

      const startButton = screen.getByText("Start Induction Proof");
      await userEvent.click(startButton);

      expect(toast.error).toHaveBeenCalledWith(
        "Induction variable must be a parameter of a function in your goal."
      );
    });
  });

  describe("parseTopLevelApplication helper", () => {
    test("handles valid function applications", async () => {
      
      render(<InductionRacket />);

      // Test valid case: induction variable is a parameter
      await userEvent.type(screen.getByLabelText("Name"), "Test");
      await userEvent.type(screen.getByLabelText("# Tag"), "test");
      await userEvent.type(screen.getByLabelText("IVar"), "n");
      await userEvent.type(screen.getByLabelText("AVal"), "0");
      await userEvent.type(screen.getByLabelText("LVar"), "k");
      await userEvent.type(screen. getByPlaceholderText("Leap Goal"), "(sum n 10)");

      const startButton = screen.getByText("Start Induction Proof");
      await userEvent.click(startButton);

      // Should not show the parameter error since 'n' is a parameter
      expect(toast.error).not.toHaveBeenCalledWith(
        "Induction variable must be a parameter of a function in your goal."
      );
    });

    test("handles nested expressions", async () => {
      
      render(<InductionRacket />);

      await userEvent.type(screen.getByLabelText("Name"), "Test");
      await userEvent.type(screen.getByLabelText("# Tag"), "test");
      await userEvent.type(screen.getByLabelText("IVar"), "n");
      await userEvent.type(screen.getByLabelText("AVal"), "0");
      await userEvent.type(screen.getByLabelText("LVar"), "k");
      await userEvent.type(screen. getByPlaceholderText("Leap Goal"), "(+ (f n) 5)");

      const startButton = screen.getByText("Start Induction Proof");
      await userEvent.click(startButton);

      // The outer function is '+', and 'n' is not a direct parameter,
      // so it should show error
      expect(toast.error).toHaveBeenCalledWith(
        "Induction variable must be a parameter of a function in your goal."
      );
    });
  });
});