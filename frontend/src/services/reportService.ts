import { apiV1 } from '../utils/api';

export interface Report {
  id: string;
  photo_id: string;
  reporter_id: string | null;
  reason: string;
  details: string | null;
  status: string;
  created_at: string;
  updated_at: string;
  resolved_at: string | null;
  resolved_by: string | null;
  resolution_notes: string | null;
}

export class ReportService {
  static async createReport(
    photoId: string,
    reason: string,
    details?: string
  ): Promise<Report> {
    return await apiV1.post('/reports/', { photo_id: photoId, reason, details });
  }

  static async getMyReports(): Promise<Report[]> {
    return await apiV1.get('/reports/my-reports');
  }
}
