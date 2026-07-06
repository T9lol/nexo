import { KeyRound } from 'lucide-react';
import {
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui';
import { API_KEY_MANAGEMENT_AVAILABLE } from '@/services';

/**
 * API key management UI. There is no backend key service, so this is disabled.
 * Key secrets are never generated, displayed, or stored in the browser.
 */
export function ApiKeysCard() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>API Keys</CardTitle>
        <CardDescription>
          Programmatic access keys for the NeXo API.
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col items-center gap-3 rounded-lg border border-dashed border-border py-8 text-center">
        <div className="flex h-11 w-11 items-center justify-center rounded-full bg-muted text-muted-foreground">
          <KeyRound className="h-5 w-5" aria-hidden="true" />
        </div>
        <p className="text-sm font-medium text-foreground">
          API key management is not available
        </p>
        <p className="max-w-sm text-xs text-muted-foreground">
          This requires a backend key service that does not exist in this build.
          For security, key secrets are never generated, displayed, or stored in
          the browser.
        </p>
        <Button
          variant="outline"
          size="sm"
          disabled={!API_KEY_MANAGEMENT_AVAILABLE}
          aria-label="Create API key"
        >
          Create API Key
        </Button>
      </CardContent>
    </Card>
  );
}
