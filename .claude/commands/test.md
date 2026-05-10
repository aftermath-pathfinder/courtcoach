# Command: /test

Run the full test suite for the layer specified, or all layers if none given.

## Usage
```
/test backend        # run pytest on backend only
/test frontend       # run vitest on frontend only
/test e2e            # run Maestro E2E flows
/test all            # run everything
```

## Steps

### backend
```bash
cd backend
pytest tests/ -v --tb=short
```
All tests must pass. If any fail, fix them before continuing. Do NOT skip or comment out failing tests.

### frontend
```bash
cd frontend
npm run typecheck && npm run lint && npm run test -- --run
```
Zero type errors. Zero lint warnings. All tests green.

### e2e
```bash
# Ensure both servers are running first:
# Terminal 1: docker-compose up (backend on :8000)
# Terminal 2: cd frontend && npm run dev (frontend on :5173)
maestro test .maestro/flows/
```

### all
Run backend → frontend → e2e in that order. Stop and fix failures before moving to next layer.

## On Failure
1. Read the full error output — don't just re-run hoping it passes
2. Fix the root cause, not the symptom
3. Re-run that layer's tests before moving on
4. If it's a known flaky test, document it in `docs/KNOWN_ISSUES.md` — do NOT delete the test
