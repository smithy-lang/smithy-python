try:
    import aiohttp

    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False


if not HAS_AIOHTTP:
    print("aiottp not found")
