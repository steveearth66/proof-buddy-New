import React, { useState } from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ProofComplete from "../components/ProofComplete";

jest.mock("react-confetti", () => {
  const React = require("react");
  return function MockConfetti() {
    return React.createElement("div", { "data-testid": "confetti-canvas" });
  };
});

/**
 * Minimal harness mirroring EquationalReasoningNew.checkCurrentProofStatus confetti logic:
 * show overlay when equationalService.checkCompletion() returns isComplete: true.
 */
function EquationalConfettiHarness({ checkCompletion }) {
  const [showProofComplete, setShowProofComplete] = useState(false);

  const checkCurrentProofStatus = async () => {
    const result = await checkCompletion();
    if (result.isComplete) {
      setShowProofComplete(true);
    } else {
      setShowProofComplete(false);
    }
  };

  return (
    <>
      <button type="button" onClick={checkCurrentProofStatus}>
        Check Current Proof
      </button>
      {showProofComplete && (
        <ProofComplete onDismiss={() => setShowProofComplete(false)} />
      )}
    </>
  );
}

/**
 * Minimal harness mirroring InductionRacket.checkCurrentProofStatus confetti logic:
 * show overlay only when BOTH base and leap check-completion calls return isComplete: true.
 */
function InductionConfettiHarness({ checkCompletionForCase }) {
  const [showProofComplete, setShowProofComplete] = useState(false);

  const checkCurrentProofStatus = async () => {
    const baseResult = await checkCompletionForCase("base");
    const leapResult = await checkCompletionForCase("leap");

    if (baseResult.isComplete && leapResult.isComplete) {
      setShowProofComplete(true);
    } else {
      setShowProofComplete(false);
    }
  };

  return (
    <>
      <button type="button" onClick={checkCurrentProofStatus}>
        Check Current Proof
      </button>
      {showProofComplete && (
        <ProofComplete onDismiss={() => setShowProofComplete(false)} />
      )}
    </>
  );
}

describe("ProofComplete confetti overlay", () => {
  test("renders celebratory overlay with confetti and dismiss message", () => {
    render(<ProofComplete onDismiss={jest.fn()} />);

    expect(screen.getByRole("heading", { name: /proof complete/i })).toBeInTheDocument();
    expect(screen.getByText(/click anywhere to dismiss/i)).toBeInTheDocument();
    expect(screen.getByTestId("confetti-canvas")).toBeInTheDocument();
    expect(document.querySelector(".confetti-overlay")).toBeInTheDocument();
  });

  test("calls onDismiss when overlay is clicked", async () => {
    const onDismiss = jest.fn();
    render(<ProofComplete onDismiss={onDismiss} />);

    await userEvent.click(document.querySelector(".confetti-overlay"));
    expect(onDismiss).toHaveBeenCalledTimes(1);
  });
});

describe("Equational proof completion → confetti", () => {
  test("shows confetti after check-completion returns isComplete: true", async () => {
    const checkCompletion = jest.fn().mockResolvedValue({
      isComplete: true,
      message: "Proof complete!",
    });

    render(<EquationalConfettiHarness checkCompletion={checkCompletion} />);

    await userEvent.click(screen.getByRole("button", { name: /check current proof/i }));

    await waitFor(() => {
      expect(screen.getByTestId("confetti-canvas")).toBeInTheDocument();
    });
    expect(checkCompletion).toHaveBeenCalledTimes(1);
  });

  test("does not show confetti when check-completion returns isComplete: false", async () => {
    const checkCompletion = jest.fn().mockResolvedValue({
      isComplete: false,
      message: "Proof incomplete",
    });

    render(<EquationalConfettiHarness checkCompletion={checkCompletion} />);

    await userEvent.click(screen.getByRole("button", { name: /check current proof/i }));

    await waitFor(() => {
      expect(checkCompletion).toHaveBeenCalledTimes(1);
    });
    expect(screen.queryByTestId("confetti-canvas")).not.toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: /proof complete/i })).not.toBeInTheDocument();
  });
});

describe("Induction proof completion → confetti", () => {
  test("shows confetti only when both base and leap are complete", async () => {
    const checkCompletionForCase = jest.fn((caseName) =>
      Promise.resolve({
        isComplete: true,
        label: caseName === "base" ? "BASE CASE" : "LEAP STEP",
      })
    );

    render(
      <InductionConfettiHarness checkCompletionForCase={checkCompletionForCase} />
    );

    await userEvent.click(screen.getByRole("button", { name: /check current proof/i }));

    await waitFor(() => {
      expect(screen.getByTestId("confetti-canvas")).toBeInTheDocument();
    });
    expect(checkCompletionForCase).toHaveBeenCalledWith("base");
    expect(checkCompletionForCase).toHaveBeenCalledWith("leap");
  });

  test("does not show confetti when only base case is complete", async () => {
    const checkCompletionForCase = jest.fn((caseName) =>
      Promise.resolve({
        isComplete: caseName === "base",
        label: caseName === "base" ? "BASE CASE" : "LEAP STEP",
      })
    );

    render(
      <InductionConfettiHarness checkCompletionForCase={checkCompletionForCase} />
    );

    await userEvent.click(screen.getByRole("button", { name: /check current proof/i }));

    await waitFor(() => {
      expect(checkCompletionForCase).toHaveBeenCalledTimes(2);
    });
    expect(screen.queryByTestId("confetti-canvas")).not.toBeInTheDocument();
  });
});
