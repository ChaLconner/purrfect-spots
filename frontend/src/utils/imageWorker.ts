/// <reference lib="webworker" />

self.onmessage = async (e: MessageEvent) => {
  const { file, options, id } = e.data;
  
  try {
    // 1. Convert File to ImageBitmap (fast, non-blocking decoding)
    const bitmap = await self.createImageBitmap(file);
    
    // 2. Calculate new dimensions
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
    
    // 3. Draw on OffscreenCanvas
    const canvas = new self.OffscreenCanvas(width, height);
    const ctx = canvas.getContext('2d');
    
    if (!ctx) {
      throw new Error('Failed to get 2d context from OffscreenCanvas');
    }
    
    ctx.drawImage(bitmap, 0, 0, width, height);
    
    // 4. Convert to Blob
    // We use options.format which should be webp by default now based on our change to imageUtils
    const format = `image/${options.format || 'webp'}`;
    const quality = (options.quality || 85) / 100;
    
    const blob = await canvas.convertToBlob({ type: format, quality });
    
    // 5. Send optimized blob back to main thread
    self.postMessage({ id, blob, success: true });
    
    // Cleanup Memory
    bitmap.close();
  } catch (err: any) {
    self.postMessage({ id, error: err.message || 'Unknown error occurred in worker', success: false });
  }
};
