import { Compass } from 'lucide-react';
import { Link } from 'react-router-dom';
import { ROUTES } from '@/app/routes';
import { Button, EmptyState } from '@/components/ui';

export default function NotFoundPage() {
  return (
    <div className="flex min-h-[60vh] items-center justify-center">
      <EmptyState
        className="border-0"
        icon={Compass}
        title="Page not found"
        description="The page you’re looking for doesn’t exist or has moved."
        action={
          <Button asChild>
            <Link to={ROUTES.dashboard}>Back to Dashboard</Link>
          </Button>
        }
      />
    </div>
  );
}
