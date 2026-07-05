import { Menu } from 'lucide-react';
import { Button } from '@/components/ui';
import { ThemeToggle } from '@/theme/theme-toggle';
import { Brand } from './brand';

interface TopNavProps {
  onOpenMobileNav: () => void;
}

/** Sticky top bar: mobile menu trigger, brand (mobile), theme control. */
export function TopNav({ onOpenMobileNav }: TopNavProps) {
  return (
    <header className="sticky top-0 z-20 flex h-16 items-center gap-3 border-b border-border bg-background/80 px-4 backdrop-blur sm:px-6">
      <Button
        variant="ghost"
        size="icon"
        className="lg:hidden"
        onClick={onOpenMobileNav}
        aria-label="Open navigation"
      >
        <Menu className="h-5 w-5" aria-hidden="true" />
      </Button>

      <div className="lg:hidden">
        <Brand />
      </div>

      <div className="flex-1" />

      <ThemeToggle />
    </header>
  );
}
