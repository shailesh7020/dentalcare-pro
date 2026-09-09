# backend/scripts/run_stress_benchmark.py
"""
DentalCare Pro - High-Concurrency Stress Benchmark Suite
Simulates 10, 25, 50, and 100 concurrent user requests to measure latency and throughput.
"""
from __future__ import annotations

import asyncio
import statistics
import time
import urllib.request
import json

TARGET_URL = "http://127.0.0.1:8000/api/v1/health/live"
CONCURRENCY_LEVELS = [10, 25, 50, 100]
TOTAL_REQUESTS_PER_LEVEL = 100


async def fetch_url(url: str) -> tuple[bool, float]:
    start = time.perf_counter()
    loop = asyncio.get_running_loop()

    def sync_request():
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200

    try:
        success = await loop.run_in_executor(None, sync_request)
        elapsed = (time.perf_counter() - start) * 1000  # ms
        return success, elapsed
    except Exception:
        elapsed = (time.perf_counter() - start) * 1000
        return False, elapsed


async def run_benchmark_level(concurrency: int, total_requests: int) -> dict:
    semaphore = asyncio.Semaphore(concurrency)

    async def sem_fetch():
        async with semaphore:
            return await fetch_url(TARGET_URL)

    t0 = time.perf_counter()
    tasks = [sem_fetch() for _ in range(total_requests)]
    results = await asyncio.gather(*tasks)
    total_time = time.perf_counter() - t0

    successes = [r[1] for r in results if r[0]]
    failures = len(results) - len(successes)

    latencies = sorted(successes) if successes else [0.0]
    p50 = statistics.median(latencies)
    p95 = latencies[int(len(latencies) * 0.95)] if len(latencies) >= 20 else latencies[-1]
    p99 = latencies[int(len(latencies) * 0.99)] if len(latencies) >= 100 else latencies[-1]

    return {
        "concurrency": concurrency,
        "total_requests": total_requests,
        "success_rate": (len(successes) / total_requests) * 100,
        "failed_requests": failures,
        "total_time_sec": round(total_time, 2),
        "throughput_req_sec": round(total_requests / total_time, 1) if total_time > 0 else 0,
        "avg_latency_ms": round(statistics.mean(latencies), 2),
        "min_latency_ms": round(min(latencies), 2),
        "max_latency_ms": round(max(latencies), 2),
        "p50_ms": round(p50, 2),
        "p95_ms": round(p95, 2),
        "p99_ms": round(p99, 2),
    }


async def main():
    print("=" * 70)
    print("DENTALCARE PRO - HIGH CONCURRENCY BENCHMARK")
    print(f"Target Endpoint: {TARGET_URL}")
    print("=" * 70)

    summary_results = []
    for level in CONCURRENCY_LEVELS:
        print(f"\n[STRESS] Simulating {level} concurrent requests ({TOTAL_REQUESTS_PER_LEVEL} total calls)...")
        res = await run_benchmark_level(level, TOTAL_REQUESTS_PER_LEVEL)
        summary_results.append(res)
        print(f"  -> Success Rate: {res['success_rate']:.1f}%")
        print(f"  -> Throughput:   {res['throughput_req_sec']} req/sec")
        print(f"  -> Avg Latency:  {res['avg_latency_ms']} ms")
        print(f"  -> p50: {res['p50_ms']} ms | p95: {res['p95_ms']} ms | p99: {res['p99_ms']} ms")

    print("\n" + "=" * 70)
    print("BENCHMARK SUMMARY TABLE")
    print("=" * 70)
    print(f"{'Concurrency':<12} | {'Success Rate':<13} | {'Throughput':<15} | {'Avg Latency':<12} | {'p95 Latency':<12}")
    print("-" * 70)
    for r in summary_results:
        t_str = f"{r['throughput_req_sec']} req/s"
        a_str = f"{r['avg_latency_ms']} ms"
        p_str = f"{r['p95_ms']} ms"
        print(f"{r['concurrency']:<12} | {r['success_rate']:<12.1f}% | {t_str:<15} | {a_str:<12} | {p_str:<12}")
    print("=" * 70)

    # Save to dist
    with open("dist/stress_benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(summary_results, f, indent=2)
    print("Results written to dist/stress_benchmark_results.json")


if __name__ == "__main__":
    asyncio.run(main())
