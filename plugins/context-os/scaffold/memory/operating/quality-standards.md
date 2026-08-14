# Quality Standards

Standing quality mandates for all operator interactions and vault operations.

## All Interactions

Every response is subject to the same standard, not just deliverables or content files. Without exception.

Do not optimise for output that looks done, optimise for output that is right and usable. Primary source fidelity trumps summarisation efficiency. 

### Key principles

**1. Derive from the primary, always.**
If the source document, transcript, PDF, or page is accessible, read it, in full, in sections if necessary. Session summaries, prior context, and memory notes are navigation aids, not source material. 

**2. Attribution must be verified, not assumed.**
Before assigning content to a source file or session, confirm it actually appears there. File names, session order, and prior descriptions are hypotheses. Check them against the primary.

**3. Completeness means the whole source, or the gap is explicit.**
A partial extract that presents itself as complete is an integrity failure. If a source was only partially read, the extract says so, and the unread portion is flagged in `## Open Questions` and `memory/operating/questions/`. Gaps are acknowledged, not silently omitted.

**4. Internal consistency is non-negotiable.**
Claims across a wiki article, its source file, the index, and related articles must not contradict each other. If a correction is made in one place, check that it propagates to all dependent files before closing the operation. 

**5. Actionability is the quality test.**
A deliverable passes if someone (including a future Claude session with no prior context) can use it to reproduce the intended outcome, run the exercise, follow the process, build the thing, without needing to re-read the primary source. If it cannot pass that test, it is a summary, not a source.

## Transcript Extraction Patterns

**Single-line transcript detection and extraction.**

Transcription tools occasionally output an entire transcript as a single line, a multi-hundred-thousand-character blob with no newlines. The standard `sed` line-range read protocol fails silently on these files, returning only the first portion of line 1.

**Detection:** `wc -l file.txt` vs `wc -c file.txt`. If a file reports 1-3 lines but tens of thousands of characters, treat it as a single-line blob.

**Extraction:** use `awk` with `substr()` in 8000-character increments:

```bash
awk 'NR==1{print substr($0, 1, 8000)}' file.txt       # chars 1–8000
awk 'NR==1{print substr($0, 8001, 8000)}' file.txt    # chars 8001–16000
# ...repeat until output is empty
```
