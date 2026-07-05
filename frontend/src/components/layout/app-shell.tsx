import { useEffect, useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { cn } from '@/lib/cn';
import { MobileNav } from './mobile-nav';
import { Sidebar } from './sidebar';
import { TopNav } from './top-nav';

const SIDEBAR_STORAGE_KEY = 'nexo-sidebar-collapsed';

/** Application shell: sidebar + top nav + routed content + mobile drawer. */
export function AppShell() {
  const [collapsed, setCollapsed] = useState<boolean>(
    () => window.localStorage.getItem(SIDEBAR_STORAGE_KEY) === 'true',
  );
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();

  useEffect(() => {
    try {
      window.localStorage.setItem(SIDEBAR_STORAGE_KEY, String(collapsed));
    } catch {
      /* storage unavailable — keep in-memory state */
    }
  }, [collapsed]);

  // Close the mobile drawer on navigation.
  useEffect(() => {
    setMobileOpen(false);
  }, [location.pathname]);

  return (
    <div className="min-h-screen bg-background">
      <Sidebar
        collapsed={collapsed}
        onToggleCollapse={() => setCollapsed((value) => !value)}
      />

      <div
        className={cn(
          'flex min-h-screen flex-col transition-[padding] duration-200',
          collapsed ? 'lg:pl-16' : 'lg:pl-64',
        )}
      >
        <TopNav onOpenMobileNav={() => setMobileOpen(true)} />
        <main className="flex-1">
          <div className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
            <Outlet />
          </div>
        </main>
      </div>

      <MobileNav open={mobileOpen} onOpenChange={setMobileOpen} />
    </div>
  );
}
