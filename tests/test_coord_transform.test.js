const test = require('node:test');
const assert = require('node:assert/strict');
const { projectPdfBBoxToCanvas } = require('../src/normen_tool/static/coord_transform.js');

test('maps PDF bbox to canvas coordinates for an unrotated page', () => {
  const rect = projectPdfBBoxToCanvas([10, 20, 30, 40], { width: 100, height: 200, rotation: 0 }, 200, 400);

  assert.deepEqual(rect, {
    left: 20,
    top: 40,
    width: 40,
    height: 40,
  });
});

test('rotates bbox coordinates when the page is rotated 90 degrees', () => {
  const rect = projectPdfBBoxToCanvas([10, 20, 30, 40], { width: 100, height: 200, rotation: 90 }, 400, 200);

  assert.equal(Math.round(rect.left), -120);
  assert.equal(Math.round(rect.top), 120);
  assert.equal(Math.round(rect.width), 80);
  assert.equal(Math.round(rect.height), 20);
});

test('rotates around the page center before scaling', () => {
  const rect = projectPdfBBoxToCanvas([10, 20, 30, 40], { width: 100, height: 200, rotation: 90 }, 400, 200);

  assert.ok(rect.left < 0);
  assert.equal(Math.round(rect.top), 120);
  assert.equal(Math.round(rect.width), 80);
  assert.equal(Math.round(rect.height), 20);
});

test('uses an explicit viewport transform when one is provided', () => {
  const rect = projectPdfBBoxToCanvas([10, 20, 30, 40], { width: 100, height: 200, rotation: 0 }, 400, 200, [2, 0, 0, 2, 10, 20]);

  assert.deepEqual(rect, {
    left: 90,
    top: 60,
    width: 160,
    height: 40,
  });
});

test('applies page rotation before viewport transforms for 270 degree pages', () => {
  const rect = projectPdfBBoxToCanvas([10, 20, 30, 40], { width: 100, height: 200, rotation: 270 }, 400, 200, [1, 0, 0, 1, 0, 0]);

  assert.equal(Math.round(rect.left), 440);
  assert.equal(Math.round(rect.top), 60);
  assert.equal(Math.round(rect.width), 80);
  assert.equal(Math.round(rect.height), 20);
});
