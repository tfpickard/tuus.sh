import { expect, test, Page } from '@playwright/test';

async function components(page: Page) {
  return JSON.parse(await page.locator('#prior-editor').getAttribute('data-components') ?? '[]');
}

async function drag(page: Page, selector: string, dx: number, dy: number) {
  const box = await page.locator(selector).boundingBox();
  if (!box) throw new Error(`Missing handle: ${selector}`);
  const x = box.x + box.width / 2;
  const y = box.y + box.height / 2;
  await page.mouse.move(x, y);
  await page.mouse.down();
  await page.mouse.move(x + dx, y + dy, { steps: 12 });
  await page.mouse.up();
}

test('add, remove, drag, resize, and reweight operate on the single prior', async ({ page }) => {
  await page.goto('/');
  expect((await components(page)).length).toBe(4);
  await drag(page, '[data-id="0"][data-role="center"]', 120, 0);
  expect((await components(page))[0].mean).toBeGreaterThan(1980);
  await drag(page, '[data-id="0"][data-role="width"]', -50, 0);
  expect((await components(page))[0].sigma).toBeLessThan(8);
  await drag(page, '[data-id="0"][data-role="weight"]', 0, -35);
  expect((await components(page))[0].weight).toBeGreaterThan(1);
  const box = await page.locator('#prior-editor').boundingBox();
  await page.mouse.click(box!.x + box!.width * 0.6, box!.y + box!.height * 0.35);
  expect((await components(page)).length).toBe(5);
  await page.locator('[data-role="remove"]').click();
  expect((await components(page)).length).toBe(4);
  await page.screenshot({ path: '../reports/editor-desktop.png', fullPage: true });
});

test('keyboard manipulation preserves legal bounds and at least one component', async ({ page }) => {
  await page.goto('/');
  const center = page.locator('[data-id="0"][data-role="center"]');
  await center.focus();
  await page.keyboard.press('ArrowRight');
  expect((await components(page))[0].mean).toBe(1976.5);
  await page.keyboard.press('Shift+ArrowLeft');
  expect((await components(page))[0].sigma).toBe(7.75);
  await page.keyboard.press('ArrowUp');
  expect((await components(page))[0].weight).toBeCloseTo(1.1);
  for (let index = 0; index < 3; index++) {
    await page.locator('[data-role="center"]').first().focus();
    await page.keyboard.press('Delete');
  }
  expect((await components(page)).length).toBe(1);
  await page.locator('[data-role="center"]').focus();
  await page.keyboard.press('Delete');
  expect((await components(page)).length).toBe(1);
});

test('rendered composite agrees with analytic backend mixture', async ({ page, request }) => {
  await page.goto('/');
  // Compare rendered ordinates with independently calculated reference samples.
  const values = await page.evaluate(() => {
    const svg = document.querySelector<SVGSVGElement>('#prior-editor')!;
    return { components: JSON.parse(svg.dataset.components!), scale: Number(svg.dataset.scale), path: document.querySelector('#composite-curve')!.getAttribute('d')! };
  });
  const matches = [...values.path.matchAll(/([\d.]+),([\d.]+)/g)];
  expect(matches.length).toBe(601);
  const reference = JSON.parse(requireReference());
  for (const index of [0, 60, 150, 320, 540, 600]) {
    const displayed = (248 - Number(matches[index][2])) / values.scale;
    expect(Math.abs(displayed - reference[index])).toBeLessThan(1e-7);
  }
});

function requireReference() {
  // Python generates this artifact from the analytic CDF, independently of the browser approximation.
  return referenceText;
}

import { readFileSync } from 'node:fs';
const referenceText = readFileSync(new URL('../../reports/default-density.json', import.meta.url), 'utf8');

for (const prefix of ['', '/tuus']) {
  test(`real synthesis, copy and re-sampling at ${prefix || '/'}`, async ({ page, context }) => {
    await context.grantPermissions(['clipboard-read', 'clipboard-write']);
    const failed: string[] = [];
    page.on('requestfailed', request => failed.push(request.url()));
    page.on('pageerror', error => failed.push(error.message));
    await page.goto(prefix + '/');
    await page.locator('#intent').fill('Ask Morgan to collect the printouts before 15:00.');
    await page.locator('#synthesize').click();
    await expect(page.locator('#output-state')).toHaveText('SYNTHESIS COMPLETE', { timeout: 110_000 });
    const output = await page.locator('#output').innerText();
    expect(output).toContain('Morgan');
    expect(output).toMatch(/\bcollect(?:s|ed|ing)?\b/i);
    expect(output).not.toMatch(/\bfrom Morgan\b/);
    expect(output).toMatch(/15:00|3\s*(?:p\.?m\.?|PM)/);
    await page.locator('#copy').click();
    expect(await page.evaluate(() => navigator.clipboard.readText())).toBe(output);
    await page.locator('#resample').click();
    await expect(page.locator('#output-state')).toHaveText('SYNTHESIS COMPLETE', { timeout: 110_000 });
    const resampled = await page.locator('#output').innerText();
    expect(resampled).toContain('Morgan');
    expect(resampled).toMatch(/\bcollect(?:s|ed|ing)?\b/i);
    expect(resampled).not.toMatch(/\bfrom Morgan\b/);
    expect(failed).toEqual([]);
    await page.screenshot({ path: `../reports/synthesis-${prefix ? 'subpath' : 'root'}.png`, fullPage: true });
  });
}

test('mobile display retains the input, prior, and output', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/tuus/');
  await expect(page.locator('#intent')).toBeVisible();
  await expect(page.locator('#prior-editor')).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);
  await page.screenshot({ path: '../reports/editor-mobile.png', fullPage: true });
});

test('service failures and user-supplied markup remain bounded', async ({ page }) => {
  await page.goto('/');
  await page.route('**/api/synthesize', route => route.fulfill({ status: 503, body: '{}' }));
  await page.locator('#intent').fill('Thank a colleague.');
  await page.locator('#synthesize').click();
  await expect(page.locator('#error')).toBeVisible();
  await expect(page.locator('#synthesize')).toBeEnabled();
  await page.unroute('**/api/synthesize');
  await page.route('**/api/synthesize', route => route.fulfill({ contentType: 'application/json', body: JSON.stringify({ utterance: '<img src=x onerror=alert(1)>' }) }));
  await page.locator('#synthesize').click();
  await expect(page.locator('#output')).toHaveText('<img src=x onerror=alert(1)>');
  expect(await page.locator('#output img').count()).toBe(0);
});
