export interface CatDetectionResult {
  has_cats: boolean;
  confidence?: number;
  detect_count?: number;
  detections?: Array<{
    label: string;
    confidence: number;
    box?: [number, number, number, number];
  }>;
  [key: string]: unknown;
}

export interface UploadResponse {
  id: string;
  url: string;
  thumbnail_url?: string;
  location_name?: string;
  description?: string;
  tags?: string[];
  user_id?: string;
  created_at?: string;
  [key: string]: unknown;
}
