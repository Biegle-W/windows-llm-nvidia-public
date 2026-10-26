# Windows NVIDIA API client handoff — October 25, 2026

Windows is the retained fallback for the i5-13600KF / 64 GB / RTX 3080 Ti host.
Native Linux NVIDIA has a separate repository, driver, credentials and future
router deployment. The dual-AMD Linux host remains independent.

Windows base URL: **http://<TAILSCALE_HOST>:10000/v1**. Supply the owner's existing
Windows API key through client credentials/LLAMA_CPP_API_KEY; no key is included.
Use authenticated `/v1/models` to discover the four current API IDs. Their current
allocated contexts are Ornith/LFM 128K and Qwen27B/Empero 64K; actual tested prompt
lengths and placement are recorded in the [Windows README](../README.md).

The owned Tailscale forwarder selects port 10000. Use OpenAI-compatible chat,
streaming and tools with an appropriately long client timeout. Windows must be
awake and its visible Start Local LLM.cmd router running. The router owns one
worker and remains single-GPU scoped; a second NVIDIA card requires an intentional
profile/guard migration. Do not restart it from a client without instruction.

The previous host self-checks do not establish remote-client reachability. Verify
tailnet permissions and an authenticated request from the actual client. No Funnel,
public port forwarding or new unauthenticated listener was enabled here. Actual
addresses, credentials and saved client state stay in ignored local data.

[Windows fallback handoff](WINDOWS-NVIDIA-HANDOFF.md),
[native Linux NVIDIA handoff](https://github.com/Biegle-W/linux-llm-nvidia-public/blob/main/docs/MIGRATION-HANDOFF.md).
