/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Base URL for the NeXo backend API. Empty = same origin (dev proxy). */
  readonly VITE_API_BASE_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
