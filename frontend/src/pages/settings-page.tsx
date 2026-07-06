import { RefreshCw } from 'lucide-react';
import { useState } from 'react';
import { Button, PageHeader } from '@/components/ui';
import { ConnectionStatus } from '@/features/dashboard/connection-status';
import {
  ApiKeysCard,
  AppearanceCard,
  CurrencyCard,
  NotificationsCard,
  ProfileCard,
  SystemInfoCard,
} from '@/features/settings';
import { usePolling } from '@/hooks/use-polling';
import {
  getSystemHealth,
  readFxPreference,
  readLocalSettings,
  writeFxPreference,
  writeLocalSettings,
  type FxPreference,
} from '@/services';

export default function SettingsPage() {
  const {
    data: health,
    status,
    error,
    lastUpdated,
    refetch,
  } = usePolling(getSystemHealth, 10_000);

  const [settings, setSettings] = useState(readLocalSettings);
  const [fx, setFx] = useState<FxPreference>(readFxPreference);

  const updateSettings = (patch: Parameters<typeof writeLocalSettings>[0]) =>
    setSettings(writeLocalSettings(patch));
  const updateFx = (preference: FxPreference) => {
    writeFxPreference(preference);
    setFx(preference);
  };

  const loading = status === 'loading';
  const disconnected = status === 'error' && !health;

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Settings"
        description="Preferences, currency, and system information."
        actions={
          <div className="flex items-center gap-3">
            <ConnectionStatus
              status={status}
              error={error}
              lastUpdated={lastUpdated}
            />
            <Button
              variant="outline"
              size="sm"
              onClick={refetch}
              aria-label="Refresh system information"
            >
              <RefreshCw className="h-4 w-4" aria-hidden="true" />
              Refresh
            </Button>
          </div>
        }
      />

      <div className="grid gap-4 lg:grid-cols-2">
        <ProfileCard
          displayName={settings.displayName}
          onDisplayNameChange={(value) =>
            updateSettings({ displayName: value })
          }
          environment={health?.environment ?? '—'}
        />
        <AppearanceCard
          language={settings.language}
          onLanguageChange={(value) => updateSettings({ language: value })}
        />
        <CurrencyCard fx={fx} onChange={updateFx} />
        <NotificationsCard />
        <ApiKeysCard />
        <SystemInfoCard
          health={health}
          loading={loading}
          error={disconnected}
        />
      </div>
    </div>
  );
}
