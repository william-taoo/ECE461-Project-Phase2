from flask import Blueprint, request, jsonify, current_app
import asyncio
import aiohttp
import time
import statistics


performance_bp = Blueprint("performance", __name__)
URL = "https://huggingface.co/arnir0/Tiny-LLM" # Replace with actual URL (EC2) with model contents
CLIENTS = 100

async def fetch_one(session, url):
    start = time.time()
    async with session.get(url) as resp:
        content = await resp.read()
        end = time.time()
        return {'status': resp.status, 'bytes': len(content), 'latency_ms': (end - start) * 1000}

async def run_round():
    timeout = aiohttp.ClientTimeout(total=600) # Allow long downloads
    connector = aiohttp.TCPConnector(limit=0) # Allow unlimited concurrent connections
    async with aiohttp.ClientSession(timeout=timeout, connector=connector) as s:
        tasks = [fetch_one(s, URL) for _ in range(CLIENTS)]
        start = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=False)
        duration = time.time() - start

    return results, duration

def summarize_results(results, duration):
    latencies = [r['latency_ms'] for r in results]
    bytes_total = sum(r['bytes'] for r in results)
    mean = statistics.mean(latencies)
    median = statistics.median(latencies)
    p99 = sorted(latencies)[min(len(latencies) - 1, int(0.99 * len(latencies)) - 1)]
    throughput_bytes_per_sec = bytes_total / duration

    return {
        'count': len(results),
        'duration_s': duration,
        'bytes_total': bytes_total,
        'throughput_Bps': throughput_bytes_per_sec,
        'mean_ms': mean,
        'median_ms': median,
        'p99_ms': p99
    }

@performance_bp.route("/performance", methods=["GET"])
def get_performance():
    print("Starting performance test")
    results, duration = asyncio.run(run_round())
    summary = summarize_results(results, duration)
    return jsonify(summary), 200
