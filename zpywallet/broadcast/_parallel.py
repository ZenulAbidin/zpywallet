import asyncio


def _run_awaitable(awaitable):
    return asyncio.run(awaitable)


async def gather_broadcast_tasks(awaitables):
    tasks = [
        asyncio.create_task(asyncio.to_thread(_run_awaitable, awaitable))
        for awaitable in awaitables
    ]
    if not tasks:
        return []
    results = await asyncio.gather(*tasks, return_exceptions=True)
    if all(isinstance(result, Exception) for result in results):
        raise results[0]
    return results
