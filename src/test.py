import asyncio
from arbor_imago import core_utils


async def main():
    print(core_utils.hash_password('password'))


if __name__ == '__main__':
    asyncio.run(main())
