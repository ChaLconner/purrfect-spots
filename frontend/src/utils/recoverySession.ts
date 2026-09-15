// Recovery credentials stay in memory and are consumed by the reset view once.
let recoveryToken: string | null = null;

export function setRecoveryToken(token: string): void {
  recoveryToken = token;
}

export function takeRecoveryToken(): string | null {
  const token = recoveryToken;
  recoveryToken = null;
  return token;
}
