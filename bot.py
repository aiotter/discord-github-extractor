import discord
from . import history


client = discord.Client()


@client.event
async def on_message(message):
    em = await client.loop.run_in_executor(
        None, history.get_history, message.content)
    if em:
        await message.channel.send(embed=em)
