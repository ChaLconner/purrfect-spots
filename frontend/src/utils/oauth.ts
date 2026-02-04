/**
 * OAuth Helper Utilities for PKCE (Proof Key for Code Exchange)
 */

export function generateCodeVerifier(): string {
  const array = new Uint8Array(32);
  crypto.getRandomValues(array);
  return base64URLEncode(array);
}

export async function generateCodeChallenge(codeVerifier: string): Promise<string> {
  const encoder = new TextEncoder();
  const data = encoder.encode(codeVerifier);
  const digest = await crypto.subtle.digest('SHA-256', data);
  return base64URLEncode(new Uint8Array(digest));
}

export function base64URLEncode(array: Uint8Array): string {
  return btoa(String.fromCodePoint(...array))
    .replaceAll('+', '-')
    .replaceAll('/', '_')
    .replaceAll('=', '');
}

/**
 * Generates the Google OAuth URL with PKCE parameters
 */
export async function getGoogleAuthUrl(
  clientId: string,
  redirectUri: string
): Promise<{ url: string; codeVerifier: string }> {
  const codeVerifier = generateCodeVerifier();
  const codeChallenge = await generateCodeChallenge(codeVerifier);

  const oauthUrl = new URL('https://accounts.google.com/o/oauth2/v2/auth');
  oauthUrl.searchParams.append('client_id', clientId);
  oauthUrl.searchParams.append('redirect_uri', redirectUri);
  oauthUrl.searchParams.append('response_type', 'code');
  oauthUrl.searchParams.append('scope', 'openid email profile');
  oauthUrl.searchParams.append('code_challenge', codeChallenge);
  oauthUrl.searchParams.append('code_challenge_method', 'S256');
  oauthUrl.searchParams.append('access_type', 'offline');
  oauthUrl.searchParams.append('prompt', 'consent');

  return {
    url: oauthUrl.toString(),
    codeVerifier,
  };
}
