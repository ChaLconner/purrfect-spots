// Dedicated worker for image optimization.
self.onmessage = async (e) => {
  if (e.origin !== '' && e.origin !== self.location.origin) {
    return;
  }

  if (!e.data || typeof e.data !== 'object') {
    return;
  }

  const { file, options, id } = e.data;
  if (!file || !id || typeof id !== 'string') {
    return;
  }
  if (!options || typeof options !== 'object') {
    return;
  }

  try {
    const bitmap = await self.createImageBitmap(file);

    let { width, height } = bitmap;
    const { maxWidth, maxHeight } = options;

    if (maxWidth && width > maxWidth) {
      height = (height * maxWidth) / width;
      width = maxWidth;
    }

    if (maxHeight && height > maxHeight) {
      width = (width * maxHeight) / height;
      height = maxHeight;
    }

    width = Math.round(width);
    height = Math.round(height);

    const canvas = new self.OffscreenCanvas(width, height);
    const ctx = canvas.getContext('2d');

    if (!ctx) {
      throw new Error('Failed to get 2d context from OffscreenCanvas');
    }

    ctx.drawImage(bitmap, 0, 0, width, height);

    const format = `image/${options.format || 'webp'}`;
    const quality = (options.quality || 85) / 100;
    const blob = await canvas.convertToBlob({ type: format, quality });

    self.postMessage({ id, blob, success: true });
    bitmap.close();
  } catch (err) {
    const error = err instanceof Error ? err.message : 'Unknown error occurred in worker';
    self.postMessage({ id, error, success: false });
  }
};
