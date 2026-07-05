import { Monitor, Moon, Sun, type LucideIcon } from 'lucide-react';
import {
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  PageHeader,
  Switch,
} from '@/components/ui';
import { useTheme, type Theme } from '@/theme/theme-context';

const THEME_OPTIONS: { value: Theme; label: string; icon: LucideIcon }[] = [
  { value: 'light', label: 'Light', icon: Sun },
  { value: 'dark', label: 'Dark', icon: Moon },
  { value: 'system', label: 'System', icon: Monitor },
];

const NOTIFICATIONS = ['Trade fills', 'Risk alerts', 'Backtest completion'];

export default function SettingsPage() {
  const { theme, setTheme } = useTheme();

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Settings"
        description="Personal preferences for the terminal."
      />

      <Card>
        <CardHeader>
          <CardTitle>Appearance</CardTitle>
          <CardDescription>
            Choose how NeXo looks. “System” follows your operating system and is
            remembered on this device.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div
            className="flex flex-wrap gap-2"
            role="group"
            aria-label="Theme"
          >
            {THEME_OPTIONS.map((option) => {
              const Icon = option.icon;
              const active = theme === option.value;
              return (
                <Button
                  key={option.value}
                  variant={active ? 'primary' : 'outline'}
                  size="sm"
                  aria-pressed={active}
                  onClick={() => setTheme(option.value)}
                >
                  <Icon className="h-4 w-4" aria-hidden="true" />
                  {option.label}
                </Button>
              );
            })}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Notifications</CardTitle>
          <CardDescription>
            Placeholder — notification preferences are configured in a later
            sprint.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col divide-y divide-border">
          {NOTIFICATIONS.map((label) => (
            <div
              key={label}
              className="flex items-center justify-between gap-4 py-4 first:pt-0 last:pb-0"
            >
              <div className="flex flex-col gap-0.5">
                <p className="text-sm font-medium text-foreground">{label}</p>
                <p className="text-xs text-muted-foreground">
                  Not yet available
                </p>
              </div>
              <Switch disabled aria-label={label} />
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
