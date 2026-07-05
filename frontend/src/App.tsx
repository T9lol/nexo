import { RouterProvider } from 'react-router-dom';
import { TooltipProvider } from '@/components/ui';
import { ThemeProvider } from '@/theme/theme-provider';
import { router } from '@/app/router';

export default function App() {
  return (
    <ThemeProvider>
      <TooltipProvider delayDuration={200}>
        <RouterProvider router={router} />
      </TooltipProvider>
    </ThemeProvider>
  );
}
