# H200 GPU Optimization Guide for Docling VLM

## Current Configuration Analysis

### ✅ Already Optimized:
- **vLLM Backend**: Using VLLM instead of Transformers (2-8x faster)
- **enforce_eager=True**: Avoiding torch.compile (no C compiler needed)
- **max_num_batched_tokens=32768**: Increased batch size
- **num_threads=32**: Good threading for H200
- **Model**: Granite Docling 258M (optimized size)

### Current Performance:
- **Cold start**: 32 seconds (one-time initialization)
- **Warm inference**: 2.5 seconds/page
- **50-page RFP**: ~2.5 minutes

---

## 🚀 Additional Optimizations for Single H200 GPU

### 1. Increase GPU Memory Utilization (Recommended)

**Current**: `gpu_memory_utilization=0.2` (20%)
**Recommended for single GPU**: `0.6-0.8` (60-80%)

H200 has 141GB HBM3e memory - you can use much more!

```python
model.extra_generation_config.update({
    "gpu_memory_utilization": 0.7,  # Use 70% of H200's 141GB
    "enforce_eager": True,
    "max_num_batched_tokens": 65536,  # Double the batch size
})
```

**Expected gain**: 10-20% faster + better batch processing

---

### 2. Increase Page Batch Size via Environment Variable

**Current**: Default `page_batch_size=4` (processes 4 pages at once)
**Recommended**: `8-16` pages for H200

Set in `docker-compose.yml`:

```yaml
environment:
  - DOCLING_PERF_PAGE_BATCH_SIZE=8  # Process 8 pages in parallel
```

**Expected gain**: 15-25% faster for multi-page documents

---

### 3. Enable KV Cache Optimization

Add to vLLM configuration:

```python
model.extra_generation_config.update({
    "gpu_memory_utilization": 0.7,
    "enforce_eager": True,
    "max_num_batched_tokens": 65536,
    "kv_cache_dtype": "auto",  # Optimize KV cache format
})
```

**Expected gain**: 5-10% memory efficiency

---

### 4. Optimize Model Length (Optional)

If your documents are mostly text-heavy (not many images):

```python
model.extra_generation_config.update({
    "max_model_len": 16384,  # Increase from default 8192
    "gpu_memory_utilization": 0.7,
    "enforce_eager": True,
    "max_num_batched_tokens": 65536,
})
```

**Expected gain**: Better handling of complex pages

---

### 5. Pre-warm Multiple Pages (Advanced)

For production, pre-warm the model with various page sizes on startup to optimize CUDA graphs.

---

## 📊 Expected Performance After Full Optimization

### Current:
- Cold start: 32s
- Warm: 2.5s/page
- 50-page: ~2.5 minutes

### Optimized:
- Cold start: 32s (same, one-time)
- Warm: **1.5-2.0s/page** (20-40% faster)
- 50-page: **1.5-2.0 minutes** (40% faster)

---

## 🔧 Implementation Priority

### High Priority (Do Now):
1. **Increase gpu_memory_utilization to 0.7** ← Biggest impact
2. **Increase max_num_batched_tokens to 65536** ← Better batching

### Medium Priority (Test After):
3. **Set DOCLING_PERF_PAGE_BATCH_SIZE=8** ← Parallel page processing
4. **Add kv_cache_dtype="auto"** ← Memory optimization

### Low Priority (Optional):
5. **Adjust max_model_len** ← Only if handling very complex pages

---

## ⚠️ Considerations

### Memory Usage:
- Current: ~15-20GB GPU memory
- Optimized: ~50-70GB GPU memory (H200 has 141GB, plenty of headroom!)

### When NOT to increase settings:
- If running multiple models on same GPU
- If GPU is shared with other workloads
- If experiencing OOM errors

### Monitoring:
Watch GPU memory during processing:
```bash
watch -n 1 nvidia-smi
```

---

## 🎯 Recommended Final Configuration

```python
# In docling_service.py
model.extra_generation_config.update({
    "gpu_memory_utilization": 0.7,      # Use 70% of H200
    "enforce_eager": True,               # No torch.compile
    "max_num_batched_tokens": 65536,    # Double batch size
    "kv_cache_dtype": "auto",           # Optimize KV cache
})
```

```yaml
# In docker-compose.yml, add to environment:
environment:
  - DOCLING_PERF_PAGE_BATCH_SIZE=8
  - DOCLING_NUM_THREADS=32
```

---

## 📈 Performance Trajectory

| Configuration | Time/Page | 50-Page Doc | GPU Memory |
|---------------|-----------|-------------|------------|
| **Transformers (original)** | 18-20s | 15 min | ~3GB |
| **vLLM basic** | 2.5s | 2.5 min | ~20GB |
| **vLLM optimized** | 1.5-2.0s | 1.5-2 min | ~60GB |

---

## 🔍 Advanced: Install C Compiler for Maximum Performance

If you want absolute maximum speed (another 20-30% gain):

**Add to Dockerfile:**
```dockerfile
RUN apt-get update && apt-get install -y \
    build-essential gcc g++ \
    && rm -rf /var/lib/apt/lists/*
```

**Then remove enforce_eager:**
```python
model.extra_generation_config.update({
    "gpu_memory_utilization": 0.7,
    # Remove: "enforce_eager": True,  # Let torch.compile work
    "max_num_batched_tokens": 65536,
})
```

**Expected:** 1.0-1.5s/page (but requires longer cold start ~60s)

---

## Summary

Your H200 is a powerhouse (141GB HBM3e, 80GB compute). Current settings are conservative. You can safely:
1. Increase GPU memory from 20% → 70%
2. Double batch size
3. Process more pages in parallel
4. Get 40-50% faster processing for free!

