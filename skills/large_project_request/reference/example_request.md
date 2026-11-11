# Example request and template

## The original request (verbatim, typos included)

Sent as the first prompt of a fork of the research session, at about 50% of a 1M context:

```text
Make an online detector: I am out of time today, so overnight, try to make a version of the lane closure detector that is good for online. It should use standard libraries like opencv, shapely's C++ version, and c++ code. Assume we can solve the problem of delivering nearby intersections and nearby railroad lanelets efficiently, even if they are not currently on the car. See if our detector can be made to run in <100ms of single CPU per image, after warmup preallocating buffers and such is done. Evne if not possible, see how close we can get. 

If that all looks good though, draft a PR that makes it part of our online pipeline, and solve the delivery problem of the HD map bits(rail, intersections, lane outlines and types) we need while reusing existing code as much as possible.
```

Steering replies that followed, over 8 hours:

```text
Regarding railroad blockages, since we have at least one or two examples (IIRC 2), why not run it on those to test?

One other thing: Instead of creating blockages, can we just trigger a reroute directly, and send in which lanelets to prefer to not use? I think this would require a small expansion to the routing API, but feels less hacky than blockage polygons. Maybe that could be another draft PR?
```

```text
Hmm. Yes, split  the flag.
Regarding keeping the route, why does the car sucessfully rebuild when we drive 10m off route then?
```

Result: four stacked draft PRs (core library, message, pipeline node, routing API extension),
about 7,700 lines, with a parity harness over 150k recorded cases. After
[/iterative-PR-review](../../iterative_pr_review/SKILL.md) the stack shrank to about 5,800 lines,
and its owner judged the core PR "almost human quality".

## Template

```text
<Goal>: <in one sentence, naming the existing prototype or research to build from>.
I am <away / out of time> until <when>, so work autonomously and make reasonable decisions.

Use <language / standard libraries / runtime>, preferring what the repo already has.
Assume <scope-cutting assumption>, but <what the PRs must still solve>.

Target: <measurable bar, e.g. latency, memory, accuracy vs the prototype>. Even if that is not
possible, get as close as you can and report how close.

If that all works: draft PRs that make it part of <target system>, off by default, reusing
existing code as much as possible. <Any component boundary that needs its own PR.>

Prove behaviour against <the prototype / recorded data> with an objective check, and report the
agreement numbers.
```
