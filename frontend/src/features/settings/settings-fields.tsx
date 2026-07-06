import { type ReactNode } from 'react';

export function InfoTile({
  label,
  value,
}: {
  label: string;
  value: ReactNode;
}) {
  return (
    <div className="flex flex-col rounded-lg border border-border p-3">
      <span className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
        {label}
      </span>
      <span className="mt-1 text-sm font-medium text-foreground">{value}</span>
    </div>
  );
}
