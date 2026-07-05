import { Wallet } from 'lucide-react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  EmptyState,
  PageHeader,
} from '@/components/ui';

export default function PortfolioPage() {
  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Portfolio"
        description="Positions, allocation, cash, and P&L breakdown."
      />

      <Card>
        <CardHeader>
          <CardTitle>Positions</CardTitle>
        </CardHeader>
        <CardContent>
          <EmptyState
            icon={Wallet}
            title="No positions to show"
            description="Open positions and allocation will appear here once portfolio data is connected."
          />
        </CardContent>
      </Card>
    </div>
  );
}
