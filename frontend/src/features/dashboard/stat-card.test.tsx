import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { StatCard } from './stat-card';

describe('StatCard', () => {
  it('renders a value and sub-line', () => {
    render(<StatCard label="Total Assets" value="RM 100.00" sub="approx" />);
    expect(screen.getByText('Total Assets')).toBeInTheDocument();
    expect(screen.getByText('RM 100.00')).toBeInTheDocument();
    expect(screen.getByText('approx')).toBeInTheDocument();
  });

  it('renders an honest unavailable placeholder', () => {
    render(
      <StatCard label="Today's PnL" unavailable unavailableHint="Pending endpoint" />,
    );
    expect(screen.getByText('Pending endpoint')).toBeInTheDocument();
  });

  it('renders skeletons while loading', () => {
    const { container } = render(<StatCard label="Total" loading />);
    expect(container.querySelector('.skeleton-shimmer')).not.toBeNull();
  });
});
