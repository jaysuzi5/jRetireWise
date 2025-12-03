# StatefulSet Patching Issue & Solution

## Problem

Kubernetes StatefulSets have immutable fields that cannot be patched after creation:
- `volumeClaimTemplates` (storage configuration)
- `serviceName`
- Other spec fields (see error message for full list)

When ArgoCD (or kubectl apply) tries to update these fields, it fails with:
```
StatefulSet.apps "prod-jretirewise-postgres" is invalid: spec: Forbidden:
updates to statefulset spec for fields other than 'replicas', 'ordinals',
'template', 'updateStrategy', 'persistentVolumeClaimRetentionPolicy' and
'minReadySeconds' are forbidden
```

## Solution

To change immutable StatefulSet fields:

1. **Delete the StatefulSet (but keep the PVC)**:
   ```bash
   kubectl delete statefulset -n jretirewise prod-jretirewise-postgres --cascade=orphan
   ```

2. **Delete the PVC if you want to recreate from scratch**:
   ```bash
   kubectl delete pvc -n jretirewise postgresql-data-prod-jretirewise-postgres-0
   ```

   Or keep the PVC to preserve data:
   ```bash
   # Skip this step to keep existing data
   ```

3. **Reapply the manifests**:
   ```bash
   kubectl apply -k k8s/overlays/prod -n jretirewise
   ```

4. **Verify the StatefulSet is created correctly**:
   ```bash
   kubectl get statefulset -n jretirewise prod-jretirewise-postgres
   kubectl get pvc -n jretirewise
   ```

## ArgoCD Integration

When using ArgoCD, there are two options:

### Option 1: Manual Sync (Recommended for now)
1. ArgoCD detects the sync failure
2. Run the deletion and re-apply steps above manually
3. Trigger a new sync in ArgoCD

### Option 2: Sync Policy Configuration (Future)
Configure the ArgoCD Application resource with:
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: jretirewise-prod
spec:
  syncPolicy:
    syncOptions:
    - RespectIgnoreDifferences=true
```

And use `.argoignore` or annotation to exclude StatefulSet from sync.

## When This Occurs

You'll need to use this procedure when changing:
- Storage size (10Gi → 20Gi, etc.)
- Storage class (nfs-client → other provisioner)
- Service name
- Volume template configuration

You can safely patch:
- `spec.replicas`
- `spec.template` (pod spec, resources, env vars, etc.)
- `spec.updateStrategy`
- `spec.minReadySeconds`

## Data Safety

The PVC (Persistent Volume Claim) preserves your data:
- Deleting the StatefulSet does NOT delete the PVC or PV
- Use `--cascade=orphan` to ensure the pod is deleted but PVC remains
- The data persists on NFS storage and will be reused when StatefulSet is recreated
