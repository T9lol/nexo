import { Inbox } from 'lucide-react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  EmptyState,
  PageHeader,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui';

const COLUMNS = ['Time', 'Symbol', 'Side', 'Quantity', 'Price'];

export default function TradesPage() {
  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Trade History"
        description="Executed fills with time, side, strategy, size, and price."
      />

      <Card>
        <CardHeader>
          <CardTitle>Recent Fills</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                {COLUMNS.map((column) => (
                  <TableHead key={column}>{column}</TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow className="hover:bg-transparent">
                <TableCell colSpan={COLUMNS.length} className="p-0">
                  <EmptyState
                    className="rounded-none border-0"
                    icon={Inbox}
                    title="No trades yet"
                    description="Executed fills will appear here once trading data is connected."
                  />
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
