# Airflow Pipeline Failure Runbook

## Purpose

This runbook explains how to investigate failed or retried Airflow data pipelines.

## Duplicate-key error after retry

### Symptoms

- An Airflow task fails during database loading.
- Airflow retries the task automatically.
- The retry fails with a duplicate-key or unique-constraint error.
- Some records may already exist in the destination table.

### Likely cause

The first task attempt inserted some records before it failed. When Airflow
retried the task, the same records were inserted again.

This usually means the pipeline is not idempotent.

## What is idempotency?

An idempotent operation can run multiple times without creating an incorrect
result.

For example, an idempotent pipeline should not create duplicate rows when the
same task is retried.

## Investigation steps

1. Review the logs from the first task attempt.
2. Check whether the first attempt inserted records before failing.
3. Search the destination table for duplicate business keys.
4. Determine whether the pipeline uses INSERT, UPSERT, or MERGE.
5. Check whether the staging table is cleared before a retry.
6. Confirm that the source file was not processed more than once.

## Recommended remediation

Use one of the following strategies:

- Use UPSERT or MERGE instead of a plain INSERT.
- Delete existing records for the processing date before reloading.
- Track processed files using a control table.
- Use a unique business key to prevent duplicate records.
- Make the pipeline safe to retry.

## Example SQL

```sql
SELECT
    campaign_id,
    report_date,
    owner_key,
    COUNT(*) AS record_count
FROM campaign_stats
GROUP BY
    campaign_id,
    report_date,
    owner_key
HAVING COUNT(*) > 1;