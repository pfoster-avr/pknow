# Evidence: what each part of the method caught

From one run on a 4-PR stack: a C++ detector core, a message, a pipeline node and a routing API
change; about 5,800 lines. The main agent was Opus 5.5 at medium effort; the reviewers, fixer and
naive readers were Fable 5.1 at xhigh effort. The core PR went from "above average for AI, far
below human" to "almost human quality", judged by its owner. The full record is in the owner's
work-knowledge repo.

| Mechanism | What it caught |
|---|---|
| Round-0 self review against the criteria | prototype-port framing in every comment; a hash-order replay used to match the prototype; ~850 lines of geometry the repo library already had; code one PR added and a later PR deleted; tiny packages and pass-through layers |
| Fresh reviewer, round 1 | reinvented robust predicates and quaternion math; magic constants that silently diverged from the message schema; a multi-frame filter that was dead at default settings |
| Fresh reviewer, round 2 | the top PR did not build: the fixer's "all tests pass" came from a log grep that missed `ERROR:`; a comment contradicting the code; a description claiming test coverage that did not exist; 8 config switches that were always true |
| Fresh reviewer, round 3 | a safety property stated in the description was not implemented for one input type |
| Fresh reviewer, round 4 | the repo's CI visibility check failed; one output field documented three different ways |
| Fresh reviewer, round 5 | main had gained a rule about where agent-written tests go; the stack was 29 commits behind |
| Fresh reviewer, round 6 | the previous round's new behaviour was wrong by construction |
| Fresh reviewer, round 7 | no MUST: stop |
| Naive reader | contradictory definitions of the core output term; topic names written two ways; an undefined "reference"; missing motivation; a definition contradiction as late as round 5 |
| Parity harness (150k recorded inputs) | proved every refactor output-neutral; counted the two intended behaviour changes (2.2% and 4 cases) |
| Fixer allowed to refuse | kept code where the suggested library had different semantics (local vs global projection, a different membership rule, a third-party library that was not reinvention) |

What did not help:
- grepping test logs for `error:` only;
- auto-format skipping untracked files;
- re-running old CI runs, which replay their original event;
- starting the session in a permission mode that denied every shell command.
