await page.waitForLoadState('networkidle');
await page.goto('/spaces/1');
// Alternatively, ensure the URL is correct and the page is fully loaded before navigating to the next URL.