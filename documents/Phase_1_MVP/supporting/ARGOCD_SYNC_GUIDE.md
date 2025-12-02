# ArgoCD Sync Configuration for jRetireWise

## Overview

The jRetireWise deployment has been configured to work with ArgoCD while handling the StatefulSet immutability constraint. This document explains how the system works and what to do if you encounter sync failures.

## Current Configuration

**ArgoCD Application:** `jretirewise-prod` (in argocd namespace)
**Repository:** https://github.com/jaysuzi5/jRetireWise
**Branch:** main
**Path:** k8s/overlays/prod

**Sync Options Enabled:**
- `CreateNamespace=true` - Automatically creates the jretirewise namespace
- `ServerSideApply=true` - Uses server-side apply for better conflict handling

## How It Works

### Normal Sync Process
1. ArgoCD detects changes in the main branch
2. For deployments, services, configmaps, secrets: Automatic sync/patch
3. For StatefulSet (PostgreSQL): See below

### StatefulSet Special Handling

The PostgreSQL StatefulSet has immutable `volumeClaimTemplates` that cannot be patched. Instead:

1. **Manual Configuration Changes** → Edit manifests in k8s/overlays/prod/
2. **Run Recreation Script** → Execute the automated fix:
   ```bash
   ./k8s/scripts/recreate-statefulset.sh jretirewise
   ```
3. **Trigger ArgoCD Sync** → Go to ArgoCD UI and click "Sync"
   - ArgoCD will sync all other resources
   - StatefulSet is preserved (cannot be patched by ArgoCD)
4. **Verification** → Check that all pods are Running and Ready

## Workflow Example

### Scenario: Change PostgreSQL Storage Size

1. **Edit Manifest:**
   ```bash
   # Edit k8s/overlays/prod/statefulset-postgres-patch.yaml
   # Change: storage: 10Gi → storage: 20Gi
   git add k8s/overlays/prod/statefulset-postgres-patch.yaml
   git commit -m "chore: Increase PostgreSQL storage to 20Gi"
   git push origin main
   ```

2. **Recreate StatefulSet Locally:**
   ```bash
   ./k8s/scripts/recreate-statefulset.sh jretirewise
   # Script will:
   # - Delete old StatefulSet (preserving PVC data)
   # - Reapply manifests with new configuration
   # - Verify PostgreSQL is ready
   ```

3. **Sync in ArgoCD:**
   - Log into ArgoCD UI
   - Find Application: `jretirewise-prod`
   - Click "Sync" button
   - Select "Synchronize"
   - ArgoCD will apply changes to all other resources

4. **Verify:**
   ```bash
   kubectl get statefulset -n jretirewise prod-jretirewise-postgres
   kubectl get pvc -n jretirewise postgresql-data-prod-jretirewise-postgres-0
   ```

## Handling Sync Failures

### If You See: "StatefulSet spec is Forbidden"

This means ArgoCD tried to patch the StatefulSet. Follow these steps:

1. **Run the Fix Script:**
   ```bash
   ./k8s/scripts/recreate-statefulset.sh jretirewise
   ```

2. **Try Sync Again:**
   - Go to ArgoCD UI
   - Click "Sync" again
   - This time it should succeed for other resources

3. **If Still Failing:**
   - Check if there are uncommitted changes in manifests
   - Ensure the PVC was properly preserved
   - Review ARGOCD_STATEFULSET_FIX.md for manual steps

### If Other Resources Won't Sync

If deployments, services, or configmaps show sync errors:

1. Check the error message in ArgoCD UI
2. Verify resources in cluster match manifests
3. For ConfigMap/Secret changes: ArgoCD should sync automatically
4. For Deployment changes: ArgoCD should update pods automatically

## Important Notes

⚠️ **Data Safety:**
- The `.argocd-ignore` file tells ArgoCD to skip the StatefulSet during auto-sync
- The PVC is never deleted, your PostgreSQL data is always preserved
- Manual recreation is safe and non-destructive

⚠️ **When NOT to Use Script:**
- Script is only for when you've made changes to StatefulSet immutable fields
- For pod spec changes (env vars, resources, images): ArgoCD can handle these
- For replica scaling: ArgoCD can handle these

## Immutable vs. Mutable Fields

**Mutable** (ArgoCD can update):
- Pod template spec (containers, env vars, resources, volumes except volumeClaimTemplates)
- Replicas count
- Update strategy
- Pod anti-affinity rules

**Immutable** (Requires script):
- volumeClaimTemplates (storage size, storage class)
- serviceName
- Some other fields listed in error message

## Automatic Sync

The application has `automated.prune=true` and `automated.selfHeal=true`, meaning:
- ArgoCD will automatically sync changes from main branch
- ArgoCD will automatically remove resources not in manifests
- If sync fails due to StatefulSet: Manual fix required via script

To disable auto-sync (manual only):
```bash
kubectl patch application -n argocd jretirewise-prod -p '{"spec":{"syncPolicy":{"automated":null}}}'
```

## Troubleshooting

### Application Shows "OutOfSync" for StatefulSet
This is expected! The StatefulSet is managed manually. ArgoCD UI will show it as OutOfSync until it matches manifests, but this is safe.

### Need to Check What Changed
```bash
# See what would be synced
kubectl diff -k k8s/overlays/prod

# See ArgoCD's view
argocd app diff jretirewise-prod
```

### Manual Sync All Resources
```bash
argocd app sync jretirewise-prod --force
```

### Check Deployment History
```bash
kubectl get application -n argocd jretirewise-prod -o jsonpath='{.status.history}' | jq
```

## Support

- For StatefulSet issues: See ARGOCD_STATEFULSET_FIX.md
- For other sync issues: Check ArgoCD UI error messages
- For script issues: Run with bash -x for debugging: `bash -x k8s/scripts/recreate-statefulset.sh`

## Related Documentation

- `.argocd-ignore` - Resources ignored during sync
- `ARGOCD_STATEFULSET_FIX.md` - Quick reference for StatefulSet errors
- `k8s/STATEFULSET_README.md` - Detailed technical documentation
- `k8s/scripts/recreate-statefulset.sh` - Automated fix script
