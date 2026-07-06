/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Base URL for the NeXo backend API. Empty = same origin (dev proxy). */
  readonly VITE_API_URL?: string;
  /** Deprecated alias for VITE_API_URL (kept for backwards compatibility). */
  readonly VITE_API_BASE_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
