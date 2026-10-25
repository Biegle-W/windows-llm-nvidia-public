# Windows model router — October 23, 2026
> Later October 23: the active catalog was consolidated to one setting per model. See [current README](../README.md). Dated trial IDs and original settings below are preserved as evidence.

The authenticated OpenAI-compatible API at `http://127.0.0.1:10000/v1` now
advertises all four downloaded models. Select an ID in a connected harness, or
set the request's `model` field. The endpoint and existing private API key are
unchanged. Ornith remains the configured default.

| Model ID | Allocated context | Role |
|---|---:|---|
| `Ornith-1.5-35B-A3B-IQ2_S` | 32,768 | Default; existing fit-target2816/no-host profile |
| `LFM2.5-24B-A2B-UD-IQ3_XXS` | 8,192 | Selectable reasoning MoE; fit-target3584/no-host |
| `Qwen3.8-27B-UD-IQ3_XXS` | 8,192 | Selectable dense model; fit-target3584/no-host |
| `Qwen3.8-35B-A3B-IQ2_M` | 8,192 | Selectable Empero distillation; fit-target3584/no-host |

All four use mixed GPU/RAM placement on the RTX3060. Empero's new 8K profile
passed a streaming smoke in this router; its earlier 32K speed measurements
describe a different configuration. No new throughput or quality benchmark was
run. Full context windows were not retested.

## Harness and API use

`Start Local LLM.cmd` opens the visible Local-LLM terminal. The lightweight router
starts without loading weights, so its catalog remains available even when
desktop memory pressure prevents model loading. DSH Desktop's saved `llamacpp`
catalog contains all four IDs; its credential route and Ornith default are
preserved. Reopen DSH if its existing window still caches the old selector.

```http
GET /v1/models
Authorization: Bearer <YOUR_EXISTING_KEY>
```

```json
{
  "model": "LFM2.5-24B-A2B-UD-IQ3_XXS",
  "messages": [{"role": "user", "content": "Hello"}],
  "max_tokens": 2048,
  "stream": true
}
```

Send that JSON to `POST /v1/chat/completions` with the same Authorization header.
`POST /v1/completions` is also forwarded. Streaming, tools and JSON response
format fields are preserved. This does not add Responses API, embeddings or an
arbitrary-model-path endpoint.

Authenticated `GET /router/status` reports the loaded model and whether a request
is in progress. `POST /router/unload` with `{}` unloads the owned worker and
returns RAM/VRAM to the desktop; the router/catalog stay available. The last
selected model otherwise stays loaded until switching, unloading or stopping.

## Switching and resource behavior

`scripts/model_router.py` owns one private llama.cpp worker on loopback10001.
Requests are serialized through the entire response, including SSE. Another
request or unload during an active request returns503 `router_busy` and
`Retry-After: 2`; it never interrupts the active stream to switch models. Clients
may retry after the current response completes.

A switch stops the previous owned process tree and waits for it to exit before
checking the requested model's own admission limits. A refused load returns an
OpenAI-shaped503 `insufficient_resources`; it does not silently fall back to
another model. The previous model may already be unloaded to free memory.
Unknown IDs return404 without changing the worker; invalid keys return401.

Ornith keeps its4GiB RAM /16GiB commit /9728MiB actual free VRAM fresh admission.
LFM keeps3/12/8192; Qwen27B keeps3.5/16/8192. The new Empero8K profile uses the
conservative4/16/9728 admission. Every load must leave at least1024MiB actual
whole-card VRAM free after readiness. The continuous guard terminates only its
owned worker if available RAM stays below0.75GiB for five seconds. Limits are not
lowered to accommodate unrelated apps. Worker authentication is separate from
the public API credential. The visible terminal's Windows Job contains the
router and worker; closing it stops the owned tree.

Thinking defaults are applied per model. DSH's obsolete global
`enable_thinking:false` override was removed while retaining unrelated settings.
LFM uses its required reasoning template, even if an old client sends that toggle;
the other profiles default to thinking off. A first request after switching also
includes model loading time.

## Validation and final state

Seven automated protocol/concurrency tests pass without loading GPU models.
They cover authentication/catalog isolation, default/reuse/switch/unload,
unknown models, tool/JSON payload preservation, resource errors, immediate SSE
forwarding and switch exclusion, and admission before spawning.

Actual DSH Desktop's installed pi-ai SDK successfully streamed the marker reply
through LFM -> Qwen27B -> Empero -> Ornith. The real API also passed a forced
tool-call/response round trip, JSON output, authentication, unknown-ID handling
and explicit unload. These are functional smokes, not general answer-quality,
full-window, load/stress, GUI-selector or remote-peer tests. The installed DSH
application was found through its real installation path; earlier reports that
could not find it remain dated evidence.

The final router was restarted and repeated launch reused the existing owned
service. It is left running idle with no model loaded. Perplexity and Quest were
terminated at the user's request; Quest's runtime service is stopped without
changing its startup type. Chrome was temporarily closed with permission and
reopened with session restoration requested. Loading after desktop apps return
still depends on the same per-model admission limits. No Linux settings, model
weights, network forwarding or credentials were changed.

See [numeric verification](verification/windows-model-router-20261023.json).
`config/selected-profiles.json` is the source registry. Regenerate with
`scripts/build_configuration.py`, then stop/start the router after changing
settings. Adding a model to the source registry does not install its weights or
establish that it fits. DSH catalog updates use
`scripts/configure_llama_harness.cjs` through Desktop's Electron Node runtime.
