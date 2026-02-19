export const REPORT_REASONS = [
  { value: 'not_a_cat', label: 'Not a Cat / Irrelevant' },
  { value: 'animal_welfare', label: 'Animal Abuse / Distress' },
  { value: 'privacy', label: 'Privacy Violation / Private Property' },
  { value: 'inappropriate', label: 'Inappropriate Content (Nudity/Gore)' },
  { value: 'spam', label: 'Spam / Advertising' },
  { value: 'harassment', label: 'Harassment / Hate Speech' },
  { value: 'other', label: 'Other' },
];

export const RESOLUTION_REASONS = [
  { value: 'violation_content', label: 'Violation: Inappropriate Content', type: 'resolved' },
  { value: 'violation_irrelevant', label: 'Violation: Not a Cat / Irrelevant', type: 'resolved' },
  { value: 'violation_safety', label: 'Violation: Safety / Animal Welfare', type: 'resolved' },
  { value: 'violation_privacy', label: 'Violation: Privacy', type: 'resolved' },
  { value: 'violation_spam', label: 'Violation: Spam', type: 'resolved' },
  { value: 'warning_issued', label: 'Warning Issued', type: 'resolved' },
  { value: 'no_violation', label: 'No Violation Found', type: 'dismissed' },
  { value: 'duplicate', label: 'Duplicate Report', type: 'dismissed' },
  { value: 'context_verified', label: 'Context Verified (Safe)', type: 'dismissed' },
];
