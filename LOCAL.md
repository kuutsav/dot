# Local Models

This document provides detailed information about running and configuring local models with Kon.

## Tested Models

| Model | Quantization | Context Length | TPS | System Specs |
| ----- | -------------- | -------------- | --- | ------------ |
| `qwen/qwen3-coder-next` | Q4_K_M | 64,000 | N/A | i7-14700F × 28, 64GB RAM, 24GB VRAM (RTX 3090) |
| `zai-org/glm-4.7-flash` | Q4_K_M | 64,000 | ~80-90 | i7-14700F × 28, 64GB RAM, 24GB VRAM (RTX 3090) |

Run a local model using llama-server with the following command:

```bash
./llama-server -m <models-dir>/GLM-4.7-Flash-GGUF/GLM-4.7-Flash-Q4_K_M.gguf -n 8192 -c 64000
```

Then start kon:

```bash
kon --model zai-org/glm-4.7-flash --provider openai --base-url http://localhost:8080/v1 --api-key ""
```

> [!NOTE]
> I was not able to run qwen-coder-next reliably on my system. Either the provider config had some issues or it's too big for my system (i'm not sure)
