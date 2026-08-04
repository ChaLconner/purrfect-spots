import type { CatLocation } from '../types/api';

export interface TagInfo {
  tag: string;
  count: number;
}

export function extractTags(description: string | null | undefined): string[] {
  if (!description) return [];
  const matches = description.match(/#[a-z0-9ก-๙]+/gi);
  if (!matches) return [];
  return [...new Set(matches.map((tag) => tag.slice(1).toLowerCase()))];
}

export function getCleanDescription(description: string | null | undefined): string {
  if (!description) return '';
  return description.replace(/\n\n#.+$/s, '').trim();
}

export function hasTag(location: CatLocation, tag: string): boolean {
  const normalizedTag = tag.toLowerCase().replace(/^#/, '');
  const tags =
    location.tags && location.tags.length > 0 ? location.tags : extractTags(location.description);
  return tags.some((candidate) => candidate.toLowerCase() === normalizedTag);
}
