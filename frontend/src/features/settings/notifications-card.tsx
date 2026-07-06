import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Switch,
} from '@/components/ui';
import { NOTIFICATION_DELIVERY_AVAILABLE } from '@/services';

const CHANNELS = ['Trade fills', 'Risk alerts', 'Backtest completion'];

export function NotificationsCard() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Notifications</CardTitle>
        <CardDescription>
          Notification delivery is not available yet — there is no backend
          notification service.
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col divide-y divide-border">
        {CHANNELS.map((channel) => (
          <div
            key={channel}
            className="flex items-center justify-between gap-4 py-4 first:pt-0 last:pb-0"
          >
            <div className="flex flex-col gap-0.5">
              <p className="text-sm font-medium text-foreground">{channel}</p>
              <p className="text-xs text-muted-foreground">Not yet available</p>
            </div>
            <Switch
              disabled={!NOTIFICATION_DELIVERY_AVAILABLE}
              aria-label={channel}
            />
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
