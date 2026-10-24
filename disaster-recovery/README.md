# Kubernetes Backup and Disaster Recovery Lab

This isolated lab uses a local kind cluster, Velero, and MinIO to back up a
Kubernetes workload and its persistent files, delete the workload namespace,
restore it, and verify the data. It does not connect to AWS or modify the
repository's EKS/GitOps environments.

This is a learning exercise, not a production backup design. MinIO runs inside
the same kind cluster as the workload, so it protects against accidental
namespace deletion but **not** loss of the cluster, its nodes, or its storage.
For production, keep backups outside the failure domain and regularly test
access controls, encryption, retention, and recovery.

## Prerequisites and cost

- Docker, kind, kubectl, Velero CLI **1.15.2**, and Python **3.10+**
- Internet access to pull images and the local-path provisioner
- No AWS account or cloud resources for the default workflow

The local cluster and images use disk and memory but do not incur cloud
charges. EKS control-plane, worker, storage, and S3 use can incur AWS charges;
this repository does not provision them for the optional EKS adaptation below.

## Local kind walkthrough (PowerShell)

Run commands from the repository root in the same PowerShell session.
If Velero CLI is not installed, download its pinned Windows release:

```powershell
$veleroVersion = "v1.15.2"
$veleroArchive = Join-Path $env:TEMP "velero-$veleroVersion-windows-amd64.tar.gz"
Invoke-WebRequest "https://github.com/vmware-tanzu/velero/releases/download/$veleroVersion/velero-$veleroVersion-windows-amd64.tar.gz" -OutFile $veleroArchive
tar -xzf $veleroArchive -C $env:TEMP
$env:PATH = (Join-Path $env:TEMP "velero-$veleroVersion-windows-amd64") + ";" + $env:PATH
velero version --client-only
```

kind, Docker, and kubectl must also be installed and available on `PATH`.

### 1. Create kind and configure persistent volumes

```powershell
kind create cluster --name dr-lab --config disaster-recovery\kind-config.yaml --wait 120s
kubectl apply -f https://raw.githubusercontent.com/rancher/local-path-provisioner/v0.0.31/deploy/local-path-storage.yaml
kubectl wait --namespace local-path-storage --for=condition=Available deployment/local-path-provisioner --timeout=120s
kubectl patch storageclass local-path --type merge -p '{"metadata":{"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'
kubectl apply -f disaster-recovery\manifests\namespaces.yaml
```

### 2. Start the local MinIO backup target

Credentials are generated at runtime and stored in a Kubernetes Secret; no
Secret manifest or credential value is committed to Git.

```powershell
$env:MINIO_ROOT_USER = "velero"
$env:MINIO_ROOT_PASSWORD = [guid]::NewGuid().ToString("N") + [guid]::NewGuid().ToString("N")
kubectl create secret generic minio-root-credentials --namespace backup-system --from-literal=MINIO_ROOT_USER=$env:MINIO_ROOT_USER --from-literal=MINIO_ROOT_PASSWORD=$env:MINIO_ROOT_PASSWORD
kubectl apply -f disaster-recovery\manifests\minio.yaml
kubectl wait --namespace backup-system --for=condition=Available deployment/minio --timeout=180s
kubectl wait --namespace backup-system --for=condition=complete job/minio-create-bucket --timeout=180s
```

Create a temporary credentials file for the Velero CLI installation:

```powershell
$credentialsFile = Join-Path $env:TEMP "dr-lab-velero-credentials"
@"
[default]
aws_access_key_id = $env:MINIO_ROOT_USER
aws_secret_access_key = $env:MINIO_ROOT_PASSWORD
"@ | Set-Content -Encoding ascii $credentialsFile
```

### 3. Install Velero and deploy the sample workload

The AWS plugin is used for its S3-compatible API; its endpoint is the in-cluster
MinIO service, not AWS. The workload manifest opts its data volume into
Velero filesystem backup.

```powershell
velero install --provider aws --plugins velero/velero-plugin-for-aws:v1.11.0 --bucket velero --secret-file $credentialsFile --backup-location-config region=minio,s3ForcePathStyle=true,s3Url=http://minio.backup-system.svc.cluster.local:9000 --use-node-agent --wait
kubectl apply -f disaster-recovery\manifests\ledger.yaml
kubectl wait --namespace ledger --for=condition=Available deployment/ledger --timeout=180s
kubectl exec --namespace ledger deployment/ledger -- sh -c "printf '%s\n' 'customer-ledger-entry-001' > /data/important.txt"
kubectl exec --namespace ledger deployment/ledger -- cat /data/important.txt
velero backup-location get
```

The backup location must show `Available`. Resolve any connection problem
before treating a backup as usable.

### 4. Back up and verify the recovery point

```powershell
velero backup create ledger-before-incident --include-namespaces ledger --wait
velero backup describe ledger-before-incident --details
velero backup logs ledger-before-incident
```

Confirm the backup completed and the `data` volume filesystem backup completed.
Do not simulate the incident until the recovery point is verified.

### 5. Delete the namespace, restore, and measure RTO

Record the expected checksum before deleting only the sample workload
namespace:

```powershell
$expectedSha256 = (kubectl exec --namespace ledger deployment/ledger -- sha256sum /data/important.txt) -split '\s+' | Select-Object -First 1
kubectl delete namespace ledger --wait=true
```

Run the restore measurement:

```powershell
$report = Join-Path $env:TEMP "dr-lab-rto-report.json"
python disaster-recovery\scripts\measure_rto.py --backup ledger-before-incident --expected-sha256 $expectedSha256 --output $report
Get-Content $report
```

RTO begins immediately before restore creation and ends only after the
deployment is Available and the restored file SHA-256 matches its
pre-incident value. It excludes detection time and the namespace deletion. The
JSON report records backup/restore names, UTC start and finish, elapsed seconds,
and expected/actual checksums. A failed restore or checksum mismatch produces
a failed report and a non-zero exit code.

For a concise incident checklist, see the [disaster recovery runbook](RUNBOOK.md).

## Cleanup

Delete the kind cluster when finished. This removes the lab and its local
backup target without affecting other kind clusters or AWS resources.

```powershell
kind delete cluster --name dr-lab
$credentialsFile = Join-Path $env:TEMP "dr-lab-velero-credentials"
Remove-Item $credentialsFile -ErrorAction SilentlyContinue
Remove-Item (Join-Path $env:TEMP "dr-lab-rto-report.json") -ErrorAction SilentlyContinue
Remove-Item Env:MINIO_ROOT_USER -ErrorAction SilentlyContinue
Remove-Item Env:MINIO_ROOT_PASSWORD -ErrorAction SilentlyContinue
```

## Optional EKS adaptation

Use a dedicated, non-production namespace; do not apply this local MinIO
configuration to EKS. Configure an external S3 bucket, encryption, retention,
least-privilege IAM for Velero, and the appropriate snapshot or filesystem
backup method for the cluster storage driver. Check plugin/Kubernetes
compatibility and organizational security requirements first. EKS, worker,
storage, and S3 use can incur AWS charges; this repository does not create
those resources.
