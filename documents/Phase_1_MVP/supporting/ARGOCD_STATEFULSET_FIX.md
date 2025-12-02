# ArgoCD Sync Failure: StatefulSet Immutable Fields

## Problem

When syncing with ArgoCD, you may see this error:

```
Failed sync attempt to 2d760f2f2cbcda7280279960207180201f2b34c6:
one or more objects failed to apply, reason: error when patching "/dev/shm/...":
StatefulSet.apps "prod-jretirewise-postgres" is invalid: spec: Forbidden:
updates to statefulset spec for fields other than 'replicas', 'ordinals',
'template', 'updateStrategy', 'persistentVolumeClaimRetentionPolicy' and
'minReadySeconds' are forbidden
```

This occurs when the manifests try to change immutable StatefulSet fields like `volumeClaimTemplates`.

## Quick Fix

### Option 1: Use the Automated Script (Recommended)

```bash
./k8s/scripts/recreate-statefulset.sh jretirewise
```

This script will:
1. Delete the StatefulSet safely (preserving your PVC data)
2. Wait for the pod to terminate
3. Reapply the manifests
4. Wait for PostgreSQL to be ready
5. Verify everything is working

### Option 2: Manual Steps

```bash
# 1. Delete StatefulSet (but keep PVC with data)
kubectl delete statefulset -n jretirewise prod-jretirewise-postgres --cascade=orphan

# 2. Reapply manifests
kubectl apply -k k8s/overlays/prod -n jretirewise

# 3. Verify PostgreSQL is ready
kubectl get statefulset -n jretirewise prod-jretirewise-postgres
kubectl get pvc -n jretirewise
```

### Option 3: From ArgoCD UI

After running the script above:
1. Go to your ArgoCD Application
2. Click "Sync"
3. The sync should now succeed

## Why This Happens

Kubernetes prevents changes to certain StatefulSet fields to avoid data loss. These immutable fields include:
- `volumeClaimTemplates` (how storage is requested)
- `serviceName`
- Some spec fields

When you change the manifests to update these fields (e.g., storage size or class), Kubernetes rejects the patch.

## Data Safety

⚠️ **Important**: The PVC (your actual data) is preserved when you delete the StatefulSet.

- The `--cascade=orphan` flag deletes the StatefulSet but leaves the PVC intact
- Your PostgreSQL data persists on the NFS storage
- When the StatefulSet is recreated, it can reuse the same PVC
- No data is lost

## Common Scenarios

### Scenario 1: Changed Storage Size
If you changed `10Gi` to `20Gi` in the manifest:
```bash
./k8s/scripts/recreate-statefulset.sh
```

### Scenario 2: Changed Storage Class
If you changed from `nfs-client` to a different provisioner:
```bash
# Delete and recreate - data preserved
./k8s/scripts/recreate-statefulset.sh
```

### Scenario 3: First Sync After Scaling Down
When you first deploy the scaled-down configuration:
```bash
./k8s/scripts/recreate-statefulset.sh
```

## Preventing Future Issues

To avoid this in the future:
1. Plan storage changes carefully before deployment
2. Document any StatefulSet changes in PR descriptions
3. Use this process when you need to change immutable fields

## More Information

See `k8s/STATEFULSET_README.md` for comprehensive documentation.

## Support

If the script doesn't work:
1. Check the error message in the pod description: `kubectl describe pod -n jretirewise prod-jretirewise-postgres-0`
2. Verify the storage provisioner exists: `kubectl get storageclass`
3. Check NFS availability: `kubectl get pv | grep nfs`
