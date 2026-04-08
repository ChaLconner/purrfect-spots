export interface CatDetected {
  description: string;
  breed_guess: string;
  position: string;
  size: string;
}

export interface CatDetectionResult {
  has_cats: boolean;
  cat_count: number;
  confidence: number;
  cats_detected: CatDetected[];
  image_quality?: string;
  suitable_for_cat_spot: boolean;
  reasoning?: string;
  note?: string;
  filename?: string;
  file_size?: number;
  detected_by?: string;
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
