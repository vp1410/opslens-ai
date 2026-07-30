# API Timeout Investigation Runbook

## Symptoms

- API requests take longer than expected.
- Clients receive HTTP 504 responses.
- Requests fail during periods of high traffic.
- Application logs show downstream timeout errors.

## Common causes

- A downstream service is responding slowly.
- A database query is taking too long.
- The connection pool is exhausted.
- The API timeout setting is too low.
- The service is overloaded.
- A network dependency is unavailable.

## Investigation steps

1. Check request latency and error-rate metrics.
2. Identify which endpoint is affected.
3. Review traces to find the slowest downstream operation.
4. Check database-query execution times.
5. Review connection-pool usage.
6. Compare the failure period with traffic levels.
7. Check whether a recent deployment changed performance.

## Recommended remediation

- Optimize slow database queries.
- Add an index where appropriate.
- Increase capacity when the service is overloaded.
- Add caching for repeated requests.
- Use retries only for safe operations.
- Configure circuit breakers for unstable downstream services.
- Adjust timeout values only after identifying the underlying issue.

## Important warning

Increasing a timeout may hide the symptom without fixing the root cause.