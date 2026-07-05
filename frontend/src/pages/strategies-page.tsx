import { BrainCircuit } from 'lucide-react';
import {
  EmptyState,
  PageHeader,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui';

export default function StrategiesPage() {
  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Strategies"
        description="Strategy roster, adaptive scores and weights, and policy selection."
      />

      <Tabs defaultValue="all">
        <TabsList>
          <TabsTrigger value="all">All</TabsTrigger>
          <TabsTrigger value="active">Active</TabsTrigger>
          <TabsTrigger value="candidates">Candidates</TabsTrigger>
        </TabsList>
        <TabsContent value="all">
          <EmptyState
            icon={BrainCircuit}
            title="No strategies loaded"
            description="The strategy roster and adaptive scores appear here in a future sprint."
          />
        </TabsContent>
        <TabsContent value="active">
          <EmptyState
            icon={BrainCircuit}
            title="No active strategy"
            description="The strategy currently receiving market events will be shown here."
          />
        </TabsContent>
        <TabsContent value="candidates">
          <EmptyState
            icon={BrainCircuit}
            title="No candidate strategies"
            description="Standby strategies evaluated by the selector will be shown here."
          />
        </TabsContent>
      </Tabs>
    </div>
  );
}
