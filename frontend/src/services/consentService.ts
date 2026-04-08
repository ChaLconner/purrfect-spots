import { apiV1 } from '../utils/api';

export interface ConsentRecord {
  consent_type: string;
  label: string;
  granted: boolean;
  granted_at: string;
  ip_address: string | null;
  version: string | null;
}

export interface ConsentVersion {
  consent_type: string;
  label: string;
  version: string;
  effective_date: string | null;
  content_hash: string | null;
}

export class ConsentService {
  static async getMyConsents(): Promise<ConsentRecord[]> {
    const result = await apiV1.get<{ consents: ConsentRecord[] }>('/consent/my-consents');
    return result.consents || [];
  }

  static async recordConsent(
    consentType: string,
    granted: boolean
  ): Promise<{ message: string; version: string }> {
    return await apiV1.post('/consent/consent', {
      consent_type: consentType,
      granted,
    });
  }
}
