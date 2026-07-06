import { Monitor, Moon, Sun, type LucideIcon } from 'lucide-react';
import {
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui';
import { AVAILABLE_LANGUAGES } from '@/services';
import { useTheme, type Theme } from '@/theme/theme-context';

const THEME_OPTIONS: { value: Theme; label: string; icon: LucideIcon }[] = [
  { value: 'light', label: 'Light', icon: Sun },
  { value: 'dark', label: 'Dark', icon: Moon },
  { value: 'system', label: 'System', icon: Monitor },
];

interface AppearanceCardProps {
  language: string;
  onLanguageChange: (language: string) => void;
}

export function AppearanceCard({
  language,
  onLanguageChange,
}: AppearanceCardProps) {
  const { theme, setTheme } = useTheme();

  return (
    <Card>
      <CardHeader>
        <CardTitle>Appearance & Language</CardTitle>
        <CardDescription>
          Theme is applied and remembered on this device.
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-5">
        <div className="flex flex-col gap-2">
          <span className="text-sm font-medium text-foreground">Theme</span>
          <div className="flex flex-wrap gap-2" role="group" aria-label="Theme">
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
        </div>

        <div className="flex flex-col gap-2">
          <label htmlFor="language" className="text-sm font-medium">
            Language
          </label>
          <Select value={language} onValueChange={onLanguageChange}>
            <SelectTrigger
              id="language"
              className="sm:w-[200px]"
              aria-label="Language"
            >
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {AVAILABLE_LANGUAGES.map((option) => (
                <SelectItem key={option.code} value={option.code}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <span className="text-[11px] text-muted-foreground">
            Additional languages are not available yet.
          </span>
        </div>
      </CardContent>
    </Card>
  );
}
