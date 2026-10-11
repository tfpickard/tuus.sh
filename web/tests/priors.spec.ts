import { expect, test } from '@playwright/test';

test('canonical tight and broad-plus-tight priors are expressible', async ({ page }) => {
  await page.goto('/');
  for (let index = 0; index < 3; index++) {
    await page.locator('[data-role="center"]').first().focus();
    await page.keyboard.press('Delete');
  }
  await page.locator('[data-role="center"]').focus();
  for (let step = 0; step < 24; step++) await page.keyboard.press('ArrowLeft');
  for (let step = 0; step < 30; step++) await page.keyboard.press('Shift+ArrowLeft');
  let components = JSON.parse(await page.locator('#prior-editor').getAttribute('data-components') ?? '[]');
  expect(components[0].mean).toBe(2012);
  expect(components[0].sigma).toBe(0.5);
  await page.screenshot({ path: '../reports/prior-tight-2012.png', fullPage: true });
  for (let step = 0; step < 30; step++) await page.keyboard.press('Shift+ArrowRight');
  await page.screenshot({ path: '../reports/prior-tail-2012.png', fullPage: true });
  for (let step = 0; step < 28; step++) await page.keyboard.press('ArrowLeft');
  for (let step = 0; step < 16; step++) await page.keyboard.press('Shift+ArrowLeft');
  const box = await page.locator('#prior-editor').boundingBox();
  await page.mouse.click(box!.x + box!.width * (30 + (2007 - 1970) / 60 * 940) / 1000,
                         box!.y + box!.height * 0.35);
  for (let step = 0; step < 6; step++) {
    await page.locator('[data-role="center"]').last().focus();
    await page.keyboard.press('Shift+ArrowLeft');
  }
  components = JSON.parse(await page.locator('#prior-editor').getAttribute('data-components') ?? '[]');
  expect(components).toHaveLength(2);
  expect(components[0].mean).toBe(1998);
  expect(components[0].sigma).toBe(4);
  expect(components[1].mean).toBeCloseTo(2007);
  expect(components[1].sigma).toBe(0.5);
  await page.screenshot({ path: '../reports/prior-internet-2007.png', fullPage: true });
});
