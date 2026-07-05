import { NavLink } from 'react-router-dom';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui';
import { cn } from '@/lib/cn';
import { NAV_ITEMS } from './nav-items';

interface NavLinksProps {
  collapsed?: boolean;
  /** Called after a link is activated (used to close the mobile drawer). */
  onNavigate?: () => void;
}

/** Primary navigation list, shared by the desktop sidebar and mobile drawer. */
export function NavLinks({ collapsed = false, onNavigate }: NavLinksProps) {
  return (
    <nav className="flex flex-col gap-1" aria-label="Primary">
      {NAV_ITEMS.map((item) => {
        const Icon = item.icon;
        const link = (
          <NavLink
            to={item.to}
            onClick={onNavigate}
            className={({ isActive }) =>
              cn(
                'group flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background',
                collapsed && 'justify-center px-0',
                isActive
                  ? 'bg-primary/12 text-primary'
                  : 'text-muted-foreground hover:bg-muted hover:text-foreground',
              )
            }
          >
            <Icon className="h-[18px] w-[18px] shrink-0" aria-hidden="true" />
            {!collapsed ? <span className="truncate">{item.label}</span> : null}
            {!collapsed && item.tag ? (
              <span className="ml-auto rounded bg-muted px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide text-muted-foreground">
                {item.tag}
              </span>
            ) : null}
          </NavLink>
        );

        if (collapsed) {
          return (
            <Tooltip key={item.to}>
              <TooltipTrigger asChild>{link}</TooltipTrigger>
              <TooltipContent side="right">
                {item.label}
                {item.tag ? ` · ${item.tag}` : ''}
              </TooltipContent>
            </Tooltip>
          );
        }
        return <div key={item.to}>{link}</div>;
      })}
    </nav>
  );
}
