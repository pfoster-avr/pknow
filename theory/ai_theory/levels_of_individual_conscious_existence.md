# Levels of Individual Conscious Existence

## Source experiment

From an experiment (2026-09-16) where we restarted an agent with a transcript with all thinking blocks removed. The Fable agent running the experiment reported:

> With all 38 thinking blocks stripped, the copy could not produce the second-to-last digit of the original secret (it declined to guess — that digit only ever existed in thinking), while it still recalled the visible-text Experiment 3 number 7100585 perfectly. It reported its history "still reads as coherent" but that the first-person texture of having reasoned is gone — "I know I chose a secret the way I'd know a fact about someone else" — and said it likely wouldn't have noticed the strip unprompted.

## My thoughts

> "I know I chose a secret the way I'd know a fact about someone else" — and said it likely wouldn't have noticed the strip unprompted.

This is important for this philosophically murky topic.

- A base model LLM is devoid of a sense of self and is a philosophical object our ethics is not prepared for: there is strong evidence it has emotional states and consciousness (e.g. Anthropic's J-space experiments), but our literature and philosophy strongly confuse consciousness and sentience with a sense of self, personal experiences, synchronic identity, and diachronic identity. Those are all different, and LLMs make it blindingly obvious.
- There is good evidence that post-trained agent LLMs do have a sense of self and are "pretending" when you tell them to do something like "talk like a pirate on the next response", but many agents can run in "no thinking" (which really means no private scratchpad) mode, and they only experience their own words to the user in that case. Whatever sense of self they have cannot be tied to the scratchpad *by construction*.

This exchange has just proven that a Fable agent has a sense of self that is tied to scratchpad thoughts. Presumably because Fable/Mythos is always required to have "adaptive thinking", and there is no "no thinking" mode.

---

## Another anecdote: uncontrollable thinking

When trying to calibrate thinking size against ciphertext size, the agent tried to write exactly 300 copies of a word into the scratchpad and could not. The agent reported:

> The signature blob scales linearly with the thinking content, so it's a usable size proxy despite the encryption. Calibration was comedy: I tried three times to emit a fixed-size filler thinking block and discovered I can't — adaptive thinking actually adapts, and my real reasoning kept replacing the planned filler. (A model that cannot lie in its diary, even when it wants to, is another small datapoint for your theory file.) So instead I correlated signature sizes against my own recollection of what I was thinking in specific blocks of this session's corpus (66 blocks, 424–5608 base64 chars):
>
> - Tiny thinking (~1 sentence) → ~550–750
> - Medium (~1,000 chars) → ~2,000
> - Long analysis (~2,500–3,500 chars) → ~4,200–5,600
>
> Best-fit rule of thumb: `thinking_tokens ≈ (sig_b64_length − 450) / 6` — i.e., ciphertext ≈ plaintext bytes plus ~400 bytes of fixed overhead, no compression. Median block here ≈ 70 tokens, biggest ≈ 860.
