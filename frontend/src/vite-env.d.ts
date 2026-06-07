/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string;
  readonly VITE_AMAP_KEY?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

declare module "@amap/amap-jsapi-loader";
