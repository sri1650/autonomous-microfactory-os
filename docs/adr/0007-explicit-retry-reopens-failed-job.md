# ADR 0007 — Explicit retry may reopen a failed job

## Status
Accepted.

## Problem
If a final task fails, the job immediately becomes FAILED. Without a narrow recovery transition, that task cannot be explicitly retried.

## Decision
Permit only FAILED task -> READY via an explicit retry command. The command reopens the job from FAILED -> RUNNING and increments the task attempt.

## Safety
No arbitrary mutation of failed jobs is allowed.
