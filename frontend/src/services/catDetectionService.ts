export interface CatDetectionResult {
  has_cats: boolean;
  cat_count: number;
  confidence: number;
  cats_detected: Array<{
    description: string;
    breed_guess: string;
    position: string;
    size: string;
  }>;
  image_quality: string;
  suitable_for_cat_spot: boolean;
  reasoning: string;
  note?: string; // เพิ่มสำหรับ fallback response
}

export interface SpotAnalysisResult {
  suitability_score: number;
  safety_factors: {
    safe_from_traffic: boolean;
    has_shelter: boolean;
    food_source_nearby: boolean;
    water_access: boolean;
    escape_routes: boolean;
  };
  environment_type: string;
  pros: string[];
  cons: string[];
  recommendations: string[];
  best_times: string[];
}

export interface CombinedAnalysisResult {
  cat_detection: CatDetectionResult;
  spot_analysis: SpotAnalysisResult;
  overall_recommendation: {
    suitable_for_cat_spot: boolean;
    confidence: number;
    summary: string;
  };
  metadata: {
    filename: string;
    file_size: number;
    analyzed_by: string;
  };
}

export class CatDetectionService {
  private baseURL = `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/detect`;

  private getAuthHeaders() {
    const token = localStorage.getItem('access_token');
    if (!token) {
      throw new Error('No authentication token found. Please login first.');
    }
    return {
      'Authorization': `Bearer ${token}`
    };
  }

  async detectCats(file: File): Promise<CatDetectionResult> {
    console.log('🔍 Detecting cats in image:', file.name);
    
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${this.baseURL}/cats`, {
        method: 'POST',
        headers: this.getAuthHeaders(),
        body: formData
      });

      console.log('📡 Cat detection response status:', response.status);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        console.error('❌ Cat detection failed:', errorData);
        throw new Error(`Cat detection failed: ${errorData.detail || response.statusText}`);
      }

      const result = await response.json();
      console.log('✅ Cat detection result:', result);
      return result;

    } catch (error) {
      console.error('🔥 Cat detection error:', error);
      throw error;
    }
  }

  async analyzeSpot(file: File): Promise<SpotAnalysisResult> {
    console.log('🏠 Analyzing spot suitability:', file.name);
    
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${this.baseURL}/spot-analysis`, {
        method: 'POST',
        headers: this.getAuthHeaders(),
        body: formData
      });

      console.log('📡 Spot analysis response status:', response.status);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        console.error('❌ Spot analysis failed:', errorData);
        throw new Error(`Spot analysis failed: ${errorData.detail || response.statusText}`);
      }

      const result = await response.json();
      console.log('✅ Spot analysis result:', result);
      return result;

    } catch (error) {
      console.error('🔥 Spot analysis error:', error);
      throw error;
    }
  }

  async combinedAnalysis(file: File): Promise<CombinedAnalysisResult> {
    console.log('🔄 Running combined analysis:', file.name);
    
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${this.baseURL}/combined`, {
        method: 'POST',
        headers: this.getAuthHeaders(),
        body: formData
      });

      console.log('📡 Combined analysis response status:', response.status);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        console.error('❌ Combined analysis failed:', errorData);
        throw new Error(`Combined analysis failed: ${errorData.detail || response.statusText}`);
      }

      const result = await response.json();
      console.log('✅ Combined analysis result:', result);
      return result;

    } catch (error) {
      console.error('🔥 Combined analysis error:', error);
      throw error;
    }
  }

  // Utility method สำหรับตรวจสอบว่า user login แล้วหรือยัง
  isAuthenticated(): boolean {
    return !!localStorage.getItem('access_token');
  }

  // Utility method สำหรับ clear auth data
  clearAuth(): void {
    localStorage.removeItem('access_token');
  }

  // Test methods ที่ไม่ต้อง authentication
  async testDetectCats(file: File): Promise<CatDetectionResult> {
    console.log('🧪 Testing cat detection (no auth):', file.name);
    
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${this.baseURL}/test-cats`, {
        method: 'POST',
        body: formData // ไม่ใส่ Authorization header
      });

      console.log('📡 Test cat detection response status:', response.status);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        console.error('❌ Test cat detection failed:', errorData);
        throw new Error(`Test detection failed: ${errorData.detail || response.statusText}`);
      }

      const result = await response.json();
      console.log('✅ Test cat detection result:', result);
      return result;

    } catch (error) {
      console.error('🔥 Test cat detection error:', error);
      throw error;
    }
  }

  async testAnalyzeSpot(file: File): Promise<SpotAnalysisResult> {
    console.log('🧪 Testing spot analysis (no auth):', file.name);
    
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${this.baseURL}/test-spot`, {
        method: 'POST',
        body: formData
      });

      console.log('📡 Test spot analysis response status:', response.status);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        console.error('❌ Test spot analysis failed:', errorData);
        throw new Error(`Test analysis failed: ${errorData.detail || response.statusText}`);
      }

      const result = await response.json();
      console.log('✅ Test spot analysis result:', result);
      return result;

    } catch (error) {
      console.error('🔥 Test spot analysis error:', error);
      throw error;
    }
  }
}

// Export singleton instance
export const catDetectionService = new CatDetectionService();