# Command: /feature

Implement a new feature end-to-end following the CourtCoach development workflow.

## Usage
```
/feature <description>
```
Example: `/feature add video compression before upload`

## Workflow (follow this order — do not skip steps)

1. **Check scope** — Read `docs/BACKLOG.md`. Is this feature in the current milestone (v0.1)? If not, add it to the backlog and stop.

2. **Define the contract** — Before writing any code, write out:
   - What does the backend endpoint receive and return? (update `docs/API.md`)
   - What TypeScript types are needed? (add to `frontend/src/types/`)
   - What does the UI look like? (describe in plain text, no code yet)

3. **Write backend first**
   - Implement the service logic
   - Write pytest unit tests
   - Run `pytest tests/unit/` — must pass before moving on

4. **Wire the API endpoint**
   - Add FastAPI route
   - Write integration test
   - Run `pytest tests/integration/` — must pass

5. **Write frontend**
   - Add API client method in `frontend/src/api/client.ts`
   - Build the React component(s)
   - Write Vitest tests
   - Run `npm run test -- --run` — must pass

6. **Write Maestro E2E flow**
   - Add `.yaml` flow file in `.maestro/flows/`
   - Run `maestro test .maestro/flows/<new-flow>.yaml`

7. **Final check**
   - Run `/test all`

8. **Update documentation**
   - Run `/doc` — the doc-writer agent will update CHANGELOG.md, BACKLOG.md, README.md, and API.md automatically
   - Review the doc changes before committing — do not skip this step
