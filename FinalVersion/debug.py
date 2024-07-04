import asyncio
import asyncapi

async def main():
    connect = await asyncapi.get_connected_repositories("FinalTrack", 100)
    print(connect)

asyncio.run(main())