import { usedBeforeHydrationScript } from './directives/preHydrationInput'

export default {
  title: '工作台',
  titleTemplate: '%s | 工作台',
  meta: [
    { charset: 'utf-8' },
    {
      name: 'viewport',
      content: 'width=device-width, initial-scale=1.0',
    },
    {
      name: 'format-detection',
      content: 'telephone=no, email=no, address=no, date=no',
    },
  ],
  // The `key` on each favicon is what allows other parts of the app (e.g. the
  // application builder's custom favicon) to override these defaults. unhead
  // dedupes `link` tags by `key`.
  link: [
    {
      rel: 'preload',
      as: 'font',
      type: 'font/woff2',
      href: '/fonts/inter/v12/UcC73FwrK3iLTeHuS_fvQtMwCp50KnMa1ZL7W0Q5nw.woff2',
      crossorigin: 'anonymous',
      key: 'inter-latin-preload',
    },
    {
      rel: 'icon',
      type: 'image/png',
      href: '/img/favicon_16.png',
      sizes: '16x16',
      key: 'favicon-16',
    },
    {
      rel: 'icon',
      type: 'image/png',
      href: '/img/favicon_32.png',
      sizes: '32x32',
      key: 'favicon-32',
    },
    {
      rel: 'icon',
      type: 'image/png',
      href: '/img/favicon_48.png',
      sizes: '64x64',
      key: 'favicon-64',
    },
    {
      rel: 'icon',
      type: 'image/png',
      href: '/img/favicon_192.png',
      sizes: '192x192',
      key: 'favicon-192',
    },
  ],
  script: [
    { key: 'used-before-hydration', innerHTML: usedBeforeHydrationScript },
  ],
}
