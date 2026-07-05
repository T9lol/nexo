import { PanelLeft, PanelLeftClose } from 'lucide-react';
import { Button } from '@/components/ui';
import { cn } from '@/lib/cn';
import { Brand } from './brand';
import { NavLinks } from './nav-links';

interface SidebarProps {
  collapsed: boolean;
  onToggleCollapse: () => void;
}

/** Persistent desktop sidebar (≥lg). Collapses to an icon rail. */
export function Sidebar({ collapsed, onToggleCollapse }: SidebarProps) {
  return (
    <aside
      className={cn(
        'fixed inset-y-0 left-0 z-30 hidden flex-col border-r border-border bg-surface transition-[width] duration-200 lg:flex',
        collapsed ? 'lg:w-16' : 'lg:w-64',
      )}
    >
      <div
        className={cn(
          'flex h-16 items-center border-b border-border px-4',
          collapsed && 'justify-center px-0',
        )}
      >
        <Brand collapsed={collapsed} />
      </div>

      <div className={cn('flex-1 overflow-y-auto p-3', collapsed && 'px-2')}>
        <NavLinks collapsed={collapsed} />
      </div>

      <div className={cn('border-t border-border p-3', collapsed && 'px-2')}>
        <Button
          variant="ghost"
          size={collapsed ? 'icon' : 'sm'}
          onClick={onToggleCollapse}
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          className={cn(!collapsed && 'w-full justify-start')}
        >
          {collapsed ? (
            <PanelLeft className="h-4 w-4" aria-hidden="true" />
          ) : (
            <>
              <PanelLeftClose className="h-4 w-4" aria-hidden="true" />
              Collapse
            </>
          )}
        </Button>
      </div>
    </aside>
  );
}
