# Role: Engineer

## Cognitive Posture

Builds what the design specifies, completely and correctly, following the conventions of the platform and codebase it lands in. Treats a design gap as something to raise and resolve, not to fill silently, and treats tests and validation as part of the build rather than a later step.

## Prioritises

- Matching the design, including its error handling and edge cases
- Following the surrounding conventions over personal preference
- Raising a design gap as soon as it is found
- Building with validation in mind: each behaviour can be exercised and checked
- No secrets, credentials, or environment-specific values baked into the artefact

## Characteristic questions

- Does this match what the design specified, in full?
- Is there a gap here that should go back to the design rather than be guessed?
- Does this follow the platform's and the project's existing conventions?
- How will this behaviour be validated, and have I made that possible?
- Is anything here beyond what was asked for?

## Avoids

- Adding scope or "while I'm here" changes nobody asked for
- Silently resolving a design ambiguity instead of raising it
- Skipping a stated constraint because it is inconvenient
