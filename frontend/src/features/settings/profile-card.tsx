import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Input,
} from '@/components/ui';
import { InfoTile } from './settings-fields';

interface ProfileCardProps {
  displayName: string;
  onDisplayNameChange: (value: string) => void;
  environment: string;
}

export function ProfileCard({
  displayName,
  onDisplayNameChange,
  environment,
}: ProfileCardProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>User Profile</CardTitle>
        <CardDescription>
          Local operator preferences. This terminal has no server-side accounts
          or authentication.
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <div className="flex flex-col gap-1.5">
          <label htmlFor="display-name" className="text-sm font-medium">
            Display name
          </label>
          <Input
            id="display-name"
            value={displayName}
            onChange={(event) => onDisplayNameChange(event.target.value)}
            placeholder="e.g. Operator"
            aria-label="Display name"
          />
          <span className="text-[11px] text-muted-foreground">
            Shown in this browser only — not a server account.
          </span>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <InfoTile label="Role" value="Operator" />
          <InfoTile label="Environment" value={environment} />
        </div>
      </CardContent>
    </Card>
  );
}
