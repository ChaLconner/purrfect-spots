# 🛡️ Branch Protection Rules - Setup Guide

This document provides step-by-step instructions for configuring branch protection rules in GitHub to ensure code quality and security for the Purrfect Spots project.

## 📋 Table of Contents

1. [Overview](#overview)
2. [Required Protection Rules](#required-protection-rules)
3. [Setup Instructions](#setup-instructions)
4. [Environment Protection](#environment-protection)
5. [Rulesets (Recommended)](#rulesets-recommended)
6. [Troubleshooting](#troubleshooting)

---

## Overview

Branch protection rules prevent force pushes, require status checks to pass before merging, and enforce code review policies. This ensures that:

- ✅ All code changes are reviewed before merging
- ✅ CI/CD checks pass before merging
- ✅ Main and production branches are protected from accidental changes
- ✅ Deployment secrets are protected

---

## Required Protection Rules

### 🔴 `main` Branch (Production)

| Setting | Value | Reason |
|---------|-------|--------|
| **Require pull request before merging** | ✅ Enabled | All changes must go through PR |
| **Required approvals** | 1 (or more for teams) | Code review is mandatory |
| **Dismiss stale reviews** | ✅ Enabled | New commits require re-review |
| **Require review from code owners** | ✅ Enabled | Domain experts must review |
| **Require status checks to pass** | ✅ Enabled | CI must pass before merge |
| **Required status checks** | See list below | Specific checks required |
| **Require branches to be up to date** | ✅ Enabled | Merge conflicts resolved |
| **Require signed commits** | ⚠️ Optional | GPG-signed commits |
| **Require linear history** | ⚠️ Optional | No merge commits |
| **Do not allow bypassing** | ✅ Enabled | Even admins must follow rules |
| **Allow force pushes** | ❌ Disabled | Prevent history rewriting |
| **Allow deletions** | ❌ Disabled | Prevent branch deletion |

### 🟡 `dev` Branch (Development/Staging)

| Setting | Value | Reason |
|---------|-------|--------|
| **Require pull request before merging** | ✅ Enabled | All changes must go through PR |
| **Required approvals** | 1 | At least one review |
| **Dismiss stale reviews** | ✅ Enabled | New commits require re-review |
| **Require status checks to pass** | ✅ Enabled | CI must pass |
| **Required status checks** | See list below | Same as main |
| **Allow force pushes** | ❌ Disabled | Prevent history rewriting |
| **Allow deletions** | ❌ Disabled | Prevent branch deletion |

### 📋 Required Status Checks

These checks must be configured as **required** before merging:

```
✅ Backend Lint and Quality
✅ Backend Unit Tests  
✅ Frontend Lint & Type Check
✅ Frontend Unit Tests
✅ Frontend Build
✅ Quality Gate
```

Optional but recommended:
```
⚠️ Backend Type Check (non-blocking)
⚠️ API Contract Check (non-blocking)
⚠️ E2E Tests (Playwright)
⚠️ Security Scan (Trivy)
```

---

## Setup Instructions

### Step 1: Navigate to Branch Protection Settings

1. Go to your repository: `https://github.com/YOUR_ORG/purrfect-spots`
2. Click **Settings** (gear icon)
3. In the left sidebar, click **Branches** under "Code and automation"

### Step 2: Add Branch Protection Rule for `main`

1. Click **Add branch protection rule**
2. Enter `main` in the "Branch name pattern" field
3. Configure the following settings:

#### Protect matching branches

- [x] **Require a pull request before merging**
  - [x] Require approvals: `1`
  - [x] Dismiss stale pull request approvals when new commits are pushed
  - [x] Require review from Code Owners
  - [ ] Restrict who can dismiss pull request reviews
  - [x] Require approval of the most recent reviewable push

- [x] **Require status checks to pass before merging**
  - [x] Require branches to be up to date before merging
  - Search and add these status checks:
    - `Backend Lint and Quality`
    - `Backend Unit Tests`
    - `Frontend Lint & Type Check`
    - `Frontend Unit Tests`
    - `Frontend Build`
    - `Quality Gate`

- [x] **Require conversation resolution before merging**

- [ ] **Require signed commits** (optional, enable if using GPG)

- [ ] **Require linear history** (optional, for cleaner git history)

- [x] **Do not allow bypassing the above settings**

- [ ] **Restrict who can push to matching branches** (optional)

#### Rules applied to everyone including administrators

- [ ] **Allow force pushes** (keep unchecked)
- [ ] **Allow deletions** (keep unchecked)

4. Click **Create** to save the rule

### Step 3: Add Branch Protection Rule for `dev`

1. Click **Add branch protection rule**
2. Enter `dev` in the "Branch name pattern"
3. Apply similar settings as `main`, but with these differences:
   - Required approvals can be `1` (less strict than main)
   - You may allow administrators to bypass (for urgent fixes)

4. Click **Create** to save the rule

---

## Environment Protection

GitHub Environments provide additional protection for deployments.

### Step 1: Create Environments

1. Go to **Settings** → **Environments**
2. Click **New environment**

#### Staging Environment

- Name: `staging`
- Protection rules:
  - [x] Required reviewers: (optional for staging)
  - Wait timer: `0` minutes
- Deployment branches: `dev` only
- Environment secrets:
  - `STAGING_API_URL`
  - `STAGING_SUPABASE_URL`
  - `STAGING_SUPABASE_KEY`

#### Production Environment

- Name: `production`
- Protection rules:
  - [x] Required reviewers: Add 1-2 team members
  - Wait timer: `5` minutes (gives time to abort if needed)
- Deployment branches: `main` only
- Environment secrets:
  - `PROD_API_URL`
  - `PROD_SUPABASE_URL`
  - `PROD_SUPABASE_KEY`

---

## Rulesets (Recommended)

GitHub Rulesets are the newer, more powerful way to manage branch protection. They offer:

- ✅ More granular control
- ✅ Can apply to multiple branches at once
- ✅ Better audit logging
- ✅ Support for tag protection

### Create a Ruleset

1. Go to **Settings** → **Rules** → **Rulesets**
2. Click **New ruleset** → **New branch ruleset**

#### Ruleset Configuration

```yaml
Name: Production Branch Protection
Enforcement status: Active
Bypass list: (empty or specific admins for emergencies)

Target branches:
  - Include: main
  - Include: dev

Rules:
  ✅ Restrict deletions
  ✅ Require linear history (optional)
  ✅ Require a pull request before merging
     - Required approvals: 1
     - Dismiss stale reviews: true
     - Require code owner review: true
  ✅ Require status checks to pass
     - Required checks:
       - Backend Lint and Quality
       - Backend Unit Tests
       - Frontend Lint & Type Check
       - Frontend Unit Tests
       - Frontend Build
       - Quality Gate
  ✅ Block force pushes
```

---

## Troubleshooting

### Status checks not appearing?

Status checks only appear after they've run at least once. Make sure to:

1. Create a PR that triggers the CI workflow
2. Wait for all checks to complete
3. Then add them to the required checks list

### Workflow not running?

Check that:

1. The workflow file is in `.github/workflows/`
2. The branch trigger includes your branch (`main`, `dev`)
3. There are no YAML syntax errors

### Need to bypass protection temporarily?

1. **Do NOT disable protection** for the branch
2. Instead, create a `hotfix/*` branch pattern with less strict rules
3. Or temporarily add yourself to the bypass list (audit this action)

---

## Quick Reference

### Branch Protection URLs

- Branch rules: `https://github.com/YOUR_ORG/purrfect-spots/settings/branches`
- Rulesets: `https://github.com/YOUR_ORG/purrfect-spots/settings/rules`
- Environments: `https://github.com/YOUR_ORG/purrfect-spots/settings/environments`

### Required Secrets for Deployment

| Secret | Environment | Description |
|--------|-------------|-------------|
| `SUPABASE_URL` | All | Supabase project URL |
| `SUPABASE_KEY` | All | Supabase anon key |
| `SUPABASE_SERVICE_ROLE_KEY` | All | Supabase service role key |
| `VERCEL_TOKEN` | Production | Vercel deployment token |
| `SLACK_WEBHOOK` | All | Slack notification webhook |

---

## ✅ Verification Checklist

After setup, verify protection is working:

- [ ] Create a test PR to `main` from a feature branch
- [ ] Verify that direct push to `main` is blocked
- [ ] Verify that merging requires approval
- [ ] Verify that status checks run and are required
- [ ] Verify that force push is blocked
- [ ] Test deployment workflow triggers correctly

---

*Last updated: 2026-01-22*
