from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


async def send_message_to_user_group(group_name, message):
    print(f"GROUP NAME: {group_name}, MESSAGE: {message}")
    channel_layer = get_channel_layer()
    await channel_layer.group_send(
        "{}".format(group_name),
        {
            "group_name": group_name,
            "type": message.get("type"),
            "data": message.get("data")
        }
    )
