# PreMortemX Risk Register

- Run ID: pmx-example-warn-release
- Created: 2026-05-06 14:06:20 UTC

## Scope Reviewed

- API release plan
- implementation summary for authentication and rate-limiting changes
- test summary covering unit and integration status
- operational readiness notes for dashboards and alerts

## Detailed Risks

- `R-01`
  Cause-event-impact: because the phased rollout plan does not define explicit rollback criteria or a named checkpoint owner, the team may continue a failing rollout too long, leading to avoidable customer impact and slower incident containment.
  Likelihood: `Medium`
  Impact: `High`
  Current risk: `Medium-High`
  Residual risk after mitigation: `Low-Medium`
  Response: `Mitigate`
  Risk owner: Release manager
  Treatment owner: Engineering lead
  Status: Open
  Review date: before production cutover
  Evidence refs: `EV-01`, `EV-04`

- `R-02`
  Cause-event-impact: because the current evidence bundle does not show refreshed negative-path validation for token refresh failures, upstream timeouts, and burst traffic behavior, a production fault may escape into release, leading to degraded reliability under real traffic.
  Likelihood: `Medium`
  Impact: `Medium-High`
  Current risk: `Medium`
  Residual risk after mitigation: `Low`
  Response: `Mitigate`
  Risk owner: Engineering lead
  Treatment owner: Test owner
  Status: Open
  Review date: before release approval
  Evidence refs: `EV-02`, `EV-05`

- `R-03`
  Cause-event-impact: because monitoring ownership and escalation thresholds are not operationally assigned, live issues may not be recognized or escalated fast enough, leading to slower detection and extended incident duration.
  Likelihood: `Medium`
  Impact: `Medium`
  Current risk: `Medium`
  Residual risk after mitigation: `Low`
  Response: `Mitigate`
  Risk owner: Operations lead
  Treatment owner: SRE or release operations owner
  Status: Open
  Review date: day before release
  Evidence refs: `EV-03`, `EV-06`

## Evidence References

- `EV-01`: release plan staged rollout section, current version dated 2026-05-06
- `EV-02`: test summary section covering integration status, current version dated 2026-05-06
- `EV-03`: operational readiness notes dashboard section, current version dated 2026-05-06
- `EV-04`: missing rollback threshold table in release plan
- `EV-05`: missing targeted negative-path test artifact for auth-refresh and rate-limit scenarios
- `EV-06`: missing named monitoring owner and escalation threshold table

## Mitigations

- `R-01`: add rollback criteria, checkpoint timing, and named approver
- `R-02`: attach or regenerate targeted failure-path test evidence
- `R-03`: document monitoring owner, alert thresholds, and first-response steps

## Unresolved Assumptions

- assumes current integration tests are recent and representative
- assumes dashboards exist and are usable during the release window
- assumes no hidden dependency change outside the inspected bundle

## Key Point Summary

- Three material risks remain. All are operational-control or evidence-completeness risks, and each has a named mitigation path, owner, and review point.
