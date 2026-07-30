# Database Error Troubleshooting Runbook

## Duplicate records

Duplicate records usually occur when an application processes the same input
more than once or when a database write is not protected by a unique business
key.

## Common causes

- A batch job was retried after partially completing.
- The same input file was processed twice.
- The application uses INSERT instead of UPSERT.
- A unique constraint is missing.
- Two workers processed the same message concurrently.

## Investigation steps

1. Identify the table and constraint mentioned in the error.
2. Determine which columns form the unique key.
3. Search for records containing the affected key.
4. Compare the creation timestamps of duplicate records.
5. Review application logs for retries or repeated requests.
6. Verify whether concurrent workers handled the same input.

## Example duplicate search

```sql
SELECT
    business_key,
    COUNT(*) AS duplicate_count
FROM target_table
GROUP BY business_key
HAVING COUNT(*) > 1;