import { cn } from '@/lib/cn';

/** NeXo wordmark + bar-chart glyph. Collapses to just the glyph. */
export function Brand({
  collapsed = false,
  className,
}: {
  collapsed?: boolean;
  className?: string;
}) {
  return (
    <div className={cn('flex items-center gap-2.5', className)}>
      <div
        className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-primary/15"
        aria-hidden="true"
      >
        <div className="flex items-end gap-[2px]">
          <span className="block h-2 w-[3px] rounded-sm bg-primary opacity-60" />
          <span className="block h-3 w-[3px] rounded-sm bg-primary opacity-80" />
          <span className="block h-4 w-[3px] rounded-sm bg-primary" />
        </div>
      </div>
      {!collapsed ? (
        <div className="flex flex-col leading-none">
          <span className="text-sm font-semibold tracking-tight">NeXo</span>
          <span className="text-[10px] uppercase tracking-widest text-muted-foreground">
            Terminal
          </span>
        </div>
      ) : null}
    </div>
  );
}
