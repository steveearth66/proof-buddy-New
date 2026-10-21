import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import Header from '../components/Header';

jest.mock('../context/AuthContext', () => ({
  useAuth: () => ({ user: null }),
}));

describe('Help menu popups', () => {
  test('shows version log details when selected', () => {
    render(
      <MemoryRouter>
        <Header />
      </MemoryRouter>
    );

    fireEvent.click(screen.getByText('Version Log'));

    expect(screen.getByText('Version: 2026-10-23 04:30')).toBeInTheDocument();
    expect(screen.getByText('Commit: updating the version log')).toBeInTheDocument();
  });

  test('shows bug report email when selected', () => {
    render(
      <MemoryRouter>
        <Header />
      </MemoryRouter>
    );

    fireEvent.click(screen.getByText('Report Bug / Feedback'));

    expect(screen.getByText(/se435@drexel\.edu/i)).toBeInTheDocument();
  });

  test('shows about text when selected', () => {
    render(
      <MemoryRouter>
        <Header />
      </MemoryRouter>
    );

    fireEvent.click(screen.getByText('About'));

    expect(
      screen.getByText(/Proof Buddy is a proof-building and reasoning support tool/i)
    ).toBeInTheDocument();
  });
});
