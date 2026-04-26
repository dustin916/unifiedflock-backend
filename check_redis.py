import os
import django
import asyncio
from channels.layers import get_channel_layer

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'church_saas.settings')
django.setup()

async def check_redis():
    channel_layer = get_channel_layer()
    print(f"Channel layer: {channel_layer}")
    if channel_layer is None:
        print("No channel layer configured.")
        return

    try:
        await channel_layer.send('test_channel', {'type': 'test.message'})
        print("Successfully sent a message to Redis.")
    except Exception as e:
        print(f"Error connecting to Redis: {e}")

if __name__ == "__main__":
    asyncio.run(check_redis())
