# Disaster Recovery Runbook

## Scope and recovery objective

This runbook restores the isolated `ledger` sample namespace from a Velero
backup stored in MinIO on the same kind cluster. It demonstrates recovery from
namespace/workload deletion only; loss of the kind cluster also loses this
backup target. Do not use this topology as a production recovery plan.

The lab measures **technical restore RTO** from Velero restore creation until
the deployment is Available and `/data/important.txt` has its pre-incident
SHA-256. It does not include detection, decision, or incident declaration
time. The recovery point is the time the chosen Velero backup was taken.

## Before an incident

1. Confirm `velero backup-location get` reports the local location as
   `Available`.
2. Create the backup and wait for it to finish:

   ```powershell
   velero backup create ledger-before-incident --include-namespaces ledger --wait
   ```

3. Inspect `velero backup describe ledger-before-incident --details` and
   `velero backup logs ledger-before-incident`. Confirm the backup completed
   and the pod's filesystem backup for volume `data` completed.
4. Record the data checksum outside the workload namespace:

   ```powershell
   $expectedSha256 = (kubectl exec --namespace ledger deployment/ledger -- sha256sum /data/important.txt) -split '\s+' | Select-Object -First 1
   ```

   Preserve the backup name and checksum for the recovery exercise.

## Incident: namespace deleted

1. Check the active context and target before changing anything:

   ```powershell
   kubectl config current-context
   velero backup get
   ```

2. Ensure the chosen backup is `Completed` and the backup location is
   `Available`. If either check fails, stop: this runbook does not cover
   rebuilding the cluster or recovering a lost backup target.
3. Start the measured restore and record its result:

   ```powershell
   $report = Join-Path $env:TEMP "dr-lab-rto-report.json"
   python disaster-recovery\scripts\measure_rto.py --backup ledger-before-incident --expected-sha256 $expectedSha256 --output $report
   Get-Content $report
   ```

   The command exits `0` only if the restore completed, the deployment became
   Available, and the restored file's checksum matched. A non-zero exit or a
   report with `"status": "failed"` is a failed recovery; inspect the report,
   `velero restore describe <restore-name> --details`, and
   `velero restore logs <restore-name>` before retrying.
4. Record the report's `recovery_time_seconds`, `started_at_utc`,
   `completed_at_utc`, backup name, and restore name. Repeated exercises should
   use the same workload and cluster sizing if comparing RTO.

## After recovery

- Confirm the expected ledger file is readable and its checksum matches.
- Save the JSON report with the exercise evidence, outside the disposable
  cluster.
- Delete the kind cluster using the cleanup commands in the
  [lab guide](README.md) when finished.

## Production adaptation notes

Before using Velero for real workloads, store backups outside the cluster and
its failure domain, configure encryption and retention, scope IAM narrowly,
choose a storage-appropriate snapshot or filesystem-backup method, and
regularly test restoration into a clean cluster. Define RPO/RTO with
stakeholders and measure the full incident timeline separately. EKS and AWS
storage/S3 usage can incur charges; this lab does not create cloud resources.
