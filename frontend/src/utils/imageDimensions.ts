/**
 * Calculate scaled image dimensions maintaining aspect ratio and bounds safety.
 */
export function calculateScaledDimensions(
  origWidth: number,
  origHeight: number,
  maxWidth?: number,
  maxHeight?: number,
  maxCanvasDim = 4096
): { width: number; height: number } {
  let width = origWidth;
  let height = origHeight;

  if (maxCanvasDim && (width > maxCanvasDim || height > maxCanvasDim)) {
    const maxDim = Math.max(width, height);
    width = Math.round((width * maxCanvasDim) / maxDim);
    height = Math.round((height * maxCanvasDim) / maxDim);
  }

  if (maxWidth && width > maxWidth) {
    height = (height * maxWidth) / width;
    width = maxWidth;
  }

  if (maxHeight && height > maxHeight) {
    width = (width * maxHeight) / height;
    height = maxHeight;
  }

  return {
    width: Math.round(width),
    height: Math.round(height),
  };
}
