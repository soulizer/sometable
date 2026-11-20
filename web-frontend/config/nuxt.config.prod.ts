/**
 * Production Nuxt configuration
 *
 * We use a direct import rather than `extends: ['./nuxt.config.base.ts']` because
 * Nuxt 3's `extends` mechanism is designed for Nuxt layers (directories containing
 * their own nuxt.config.ts, app.vue, pages/, etc.), not for importing individual
 * config files directly.
 *
 * When pointing `extends` to a .ts file, Nuxt shows:
 *   "WARN Cannot extend config from ./nuxt.config.base.ts"
 *
 * By using a standard ES module import/export, we achieve the same result reliably.
 */

import baseConfig from './nuxt.config.base.ts'
const buildSourcemaps = process.env.NUXT_BUILD_SOURCEMAP === 'true'

export default {
  ...baseConfig,
  nitro: {
    ...baseConfig.nitro,
    // Precompress the static assets at build time, so that they're served with
    // brotli or gzip even when no compressing reverse proxy is in front.
    compressPublicAssets: { gzip: true, brotli: true },
  },
  // Sourcemap generation roughly doubles bundler memory usage and is only
  // useful when uploading maps to an error tracker (e.g. Sentry). Enable it
  // explicitly with NUXT_BUILD_SOURCEMAP=true on machines that can afford it.
  sourcemap: {
    server: buildSourcemaps,
    client: buildSourcemaps,
  },
}
