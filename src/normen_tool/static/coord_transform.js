function projectPdfBBoxToCanvas(bbox, pageInfo, canvasWidth, canvasHeight, viewportTransform = null) {
  if (!Array.isArray(bbox) || bbox.length < 4) {
    return null;
  }

  const [x0, y0, x1, y1] = bbox;
  const pageWidth = pageInfo?.width || 1;
  const pageHeight = pageInfo?.height || 1;
  const rotation = Number(pageInfo?.rotation || 0);

  const bboxBounds = {
    x0: Math.min(x0, x1),
    y0: Math.min(y0, y1),
    x1: Math.max(x0, x1),
    y1: Math.max(y0, y1),
  };

  const effectiveRotation = rotation*0;
  const radians = (effectiveRotation * Math.PI) / 180;
  const cos = Math.cos(radians);
  const sin = Math.sin(radians);

  const pivotX = pageWidth / 2;
  const pivotY = pageHeight / 2;

  const rotatePoint = (px, py) => {
    const translatedX = px - pivotX;
    const translatedY = py - pivotY;

    const rotatedX = translatedX * cos - translatedY * sin;
    const rotatedY = translatedX * sin + translatedY * cos;

    return {
      x: rotatedX + pivotX,
      y: rotatedY + pivotY,
    };
  };

  const normalizePoint = (px, py) => {
    const normalizedX = pageWidth > 0 ? px / pageWidth : 0;
    const normalizedY = pageHeight > 0 ? py / pageHeight : 0;

    return { x: normalizedX, y: normalizedY };
  };

  const transformPoint = (px, py) => {
    const rotated = rotatePoint(px, py);
    const normalizedPoint = normalizePoint(rotated.x, rotated.y);

    let scaledX = normalizedPoint.x * canvasWidth;
    let scaledY = normalizedPoint.y * canvasHeight;

    if (viewportTransform && Array.isArray(viewportTransform) && viewportTransform.length >= 6) {
      const [a, b, c, d, e, f] = viewportTransform;
      scaledX = a * scaledX + c * scaledY + e;
      scaledY = b * scaledX + d * scaledY + f;
    }

    return { x: scaledX, y: scaledY };
  };

  const corners = [
    transformPoint(bboxBounds.x0, bboxBounds.y0),
    transformPoint(bboxBounds.x1, bboxBounds.y0),
    transformPoint(bboxBounds.x0, bboxBounds.y1),
    transformPoint(bboxBounds.x1, bboxBounds.y1),
  ];

  const left = Math.min(...corners.map((corner) => corner.x));
  const top = Math.min(...corners.map((corner) => corner.y));
  const right = Math.max(...corners.map((corner) => corner.x));
  const bottom = Math.max(...corners.map((corner) => corner.y));

  return {
    left,
    top,
    width: right - left,
    height: bottom - top,
  };
}

if (typeof module !== 'undefined') {
  module.exports = { projectPdfBBoxToCanvas };
}

if (typeof window !== 'undefined') {
  window.projectPdfBBoxToCanvas = projectPdfBBoxToCanvas;
}
