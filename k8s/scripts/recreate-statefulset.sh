#!/bin/bash

# Recreate StatefulSet when immutable fields need to be updated
# This script safely deletes the StatefulSet while preserving data

set -e

NAMESPACE="${1:-jretirewise}"
STATEFULSET="prod-jretirewise-postgres"
PVC_NAME="postgresql-data-${STATEFULSET}-0"

echo "=== StatefulSet Recreation Script ==="
echo "Namespace: $NAMESPACE"
echo "StatefulSet: $STATEFULSET"
echo ""

# Check if StatefulSet exists
if ! kubectl get statefulset -n "$NAMESPACE" "$STATEFULSET" &>/dev/null; then
    echo "StatefulSet not found in namespace $NAMESPACE"
    exit 1
fi

echo "⚠️  WARNING: This will delete the StatefulSet and its pod"
echo "✅ Your data will be preserved in the PVC"
echo ""
read -p "Continue? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Cancelled"
    exit 0
fi

echo ""
echo "Step 1: Deleting StatefulSet (preserving PVC)..."
kubectl delete statefulset -n "$NAMESPACE" "$STATEFULSET" --cascade=orphan

echo "Waiting for pod to terminate..."
for i in {1..30}; do
    if ! kubectl get pod -n "$NAMESPACE" "${STATEFULSET}-0" &>/dev/null; then
        echo "✅ Pod terminated"
        break
    fi
    echo "  Waiting... ($i/30)"
    sleep 2
done

echo ""
echo "Step 2: Verifying PVC preservation..."
if kubectl get pvc -n "$NAMESPACE" "$PVC_NAME" &>/dev/null; then
    PVC_STATUS=$(kubectl get pvc -n "$NAMESPACE" "$PVC_NAME" -o jsonpath='{.status.phase}')
    echo "✅ PVC preserved (Status: $PVC_STATUS)"
else
    echo "⚠️  PVC not found - data may need to be restored"
fi

echo ""
echo "Step 3: Recreating StatefulSet from manifests..."
kubectl apply -k "$(dirname "$0")/../overlays/prod" -n "$NAMESPACE"

echo ""
echo "Step 4: Waiting for StatefulSet to be ready..."
kubectl wait --for=condition=ready pod -n "$NAMESPACE" -l "app=jretirewise,component=postgres" --timeout=300s

echo ""
echo "✅ StatefulSet recreated successfully"
echo ""
kubectl get statefulset -n "$NAMESPACE" "$STATEFULSET"
kubectl get pvc -n "$NAMESPACE" "$PVC_NAME"
