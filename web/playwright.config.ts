import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  timeout: 120_000,
  workers: 1,
  use: { baseURL: 'http://127.0.0.1:8000', viewport: { width: 1280, height: 1400 } },
  reporter: [['list'], ['json', { outputFile: '../reports/browser-results.json' }]],
});
