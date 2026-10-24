# ADR 0006 — Robot goal occupancy persists through the planning horizon

## Status
Accepted.

## Problem
A route may reach a currently-free goal that another planned robot reserves later. Treating arrival as terminal can create a future occupancy conflict.

## Decision
A path is only accepted at a goal if the robot can safely hold that cell for the remaining planning horizon.

## Consequence
Robots remain physical occupants after arrival rather than disappearing at their goals.
