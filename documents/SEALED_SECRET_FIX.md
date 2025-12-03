# Sealed Secret Unsealing Issue - Analysis & Resolution

**Date:** 2025-12-03
**Status:** Security Violation Fixed - Sealed Secret Still Needs Resolution

## Issue Summary

**Security Error Found:**
- Commit `641b760` added plaintext secrets to `k8s/base/secret.yaml`
- This violated the security architecture: plaintext secrets should ONLY be in `.gitignore`d `secrets_plain_text.yaml`
- **Action Taken:** Reverted commit with `df9585b` - sealed secret restored

**Current Problem:**
- Sealed secret cannot be unsealed by cluster
- ArgoCD error: `Failed to unseal: no key could decrypt secret`
- Root Cause: Sealed secret was encrypted with a different sealing key than cluster's current key

## Architecture

### Correct Setup (Current Goal)
```
secrets_plain_text.yaml (.gitignore)
    ↓ (encrypt with kubeseal)
k8s/base/secret.yaml (SealedSecret, encrypted)
    ↓ (deploy to cluster)
sealed-secrets-controller (in kube-system)
    ↓ (decrypt with sealing key)
Regular Kubernetes Secret in jretirewise namespace
```

### Current Problem
- `secret.yaml` is a SealedSecret
- Cluster's sealing key cannot decrypt it
- Sealed-secrets controller is running and operational
- But the encryption key is a mismatch

## Investigation Results

**Cluster Status:**
```
✓ Sealed-secrets-controller: Running (kube-system)
✓ Namespace: jretirewise exists
✓ Deployment: Uses correct namespace in kustomization.yaml
✗ Sealed Secret: Cannot be decrypted
```

## Resolution Options

### Option A: Regenerate Sealed Secret (RECOMMENDED)

**Approach:**
1. Obtain the sealing key from your cluster environment
2. Regenerate the sealed secret using current cluster's sealing key:
   ```bash
   # On a machine with kubeseal CLI installed
   kubeseal --controller-namespace kube-system --format yaml \
     < k8s/base/secrets_plain_text.yaml \
     > k8s/base/secret.yaml
   ```
3. Commit the newly sealed secret
4. ArgoCD will automatically unseal and deploy

**Pros:**
- Most secure - plaintext never in git
- Follows sealed-secrets best practices
- Proper secret management

**Cons:**
- Requires sealing key access
- Requires kubeseal CLI locally

### Option B: Use Regular Kubernetes Secret

**Approach:**
1. Create a regular Kubernetes Secret (plaintext in cluster, encrypted in transit)
2. Replace SealedSecret with Secret in `k8s/base/secret.yaml`
3. Keep plaintext template in `.gitignore`d `secrets_plain_text.yaml`

**Format:**
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: jretirewise-secret
  namespace: jretirewise
  labels:
    app: jretirewise
type: Opaque
stringData:
  # All secret keys here
```

**Pros:**
- Simple, works immediately
- No encryption/decryption complexity
- Good for home lab/dev

**Cons:**
- Plaintext in cluster (though encrypted in etcd)
- Slightly less secure than sealed secrets
- Different from production best practice

### Option C: Use External Secret Management

**Tools:** Vault, External Secrets Operator, Cloud provider secrets, etc.

- Out of scope for this fix
- More complex infrastructure
- Better for production at scale

## Recommendation

**For Current Situation:** Option A (Regenerate with correct sealing key)

**Why:** This maintains your original security architecture intent while fixing the mismatch.

**Action Steps:**
1. Extract or confirm access to sealing key
2. Run kubeseal with correct namespace parameter
3. Commit updated `secret.yaml`
4. Push to GitHub
5. ArgoCD automatically syncs and unseals secrets

## Files Involved

- `k8s/base/secret.yaml` - Current sealed secret (needs fix)
- `k8s/base/secrets_plain_text.yaml` - Plaintext template (in .gitignore)
- `.gitignore` - ✅ Correctly includes `secrets_plain_text.yaml`
- `k8s/overlays/prod/kustomization.yaml` - Namespace correctly set to `jretirewise`

## Next Steps

Once you decide on approach:

**For Option A:**
1. Provide sealing key or confirmation it's available
2. I'll regenerate the sealed secret
3. Test ArgoCD sync

**For Option B:**
1. Create a wrapper Secret instead of SealedSecret
2. Test deployment
3. Update architecture documentation

---

**Previous Commit:** `df9585b` - Reverted plaintext secret breach
**Issue Resolved:** Security architecture restored
**Remaining:** Sealed secret unsealing configuration
