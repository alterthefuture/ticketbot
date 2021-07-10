from discord.ext.commands import has_permissions, MissingPermissions
from discord.ext import commands
import discord 

import asyncio
import time
import json
import aiofiles

client = commands.Bot(command_prefix="!")
client.remove_command(name="help")

client.ticket_configs = {}

@client.event
async def on_ready():

    data = read_json("blacklist")
    client.blacklisted_users = data["blacklistedUsers"]
    
    for file in ["ticket_configs.txt"]:
        async with aiofiles.open(file, mode="a") as temp:
            pass

    async with aiofiles.open("ticket_configs.txt", mode="r") as file:
        lines = await file.readlines()
        for line in lines:
            data = line.split(" ")
            client.ticket_configs[int(data[0])] = [int(data[1]), int(data[2]), int(data[3])]

    print("Bot Is Ready.")

def read_json(filename):
    with open(f"{filename}.json","r") as file:
        data = json.load(file)
    return data

def write_json(data, filename):
    with open(f"{filename}.json", "w") as file:
        json.dump(data, file, indent=4)

@client.command()
async def help(ctx):
    embed=discord.Embed(title="Ticket Bot",description="Make sure the category has the permission `View channels` off.")
    embed.add_field(name="`!setup [message ID] [category ID]`",value="Setups the ticket system.",inline=False)
    embed.add_field(name="`!config`",value="Shows the ticket systems configuration.")
    embed.add_field(name="`!blacklist [@user]`",value="Blacklist mentioned user from creating a ticket.",inline=False)
    embed.add_field(name="`!unblacklist [@user]`",value="Unblacklist a blacklisted user.",inline=False)
    embed.set_footer(text="Made by lxy#5676")

    await ctx.send(embed=embed)

@client.command()
@commands.has_permissions(administrator=True)
async def config(ctx):
    try:
        msg_id, channel_id, category_id = client.ticket_configs[ctx.guild.id]

    except KeyError:
        embed=discord.Embed(title="Ticket Error",description="Ticket system has not been setup.",color=discord.Color.red())
        embed.set_footer(text="Made by lxy#5676")
        await ctx.send(embed=embed)

    else:
        embed=discord.Embed(title="Ticket System",description=f"**Message ID:** {msg_id}\n**Category ID:** {category_id}")
        embed.set_footer(text="Made by lxy#5676")
        await ctx.send(embed=embed)

@client.event
async def on_raw_reaction_add(payload):

    if payload.member.id in client.blacklisted_users:
        return

    if payload.member.id != client.user.id and str(payload.emoji) == u"\U0001F3AB":
        msg_id, channel_id, category_id = client.ticket_configs[payload.guild_id]

        if payload.message_id == msg_id:
            guild = client.get_guild(payload.guild_id)

            for category in guild.categories:
                if category.id == category_id:
                    break

            channel = guild.get_channel(channel_id)

            ticket_num = 1 if len(category.channels) == 0 else int(category.channels[-1].name.split("-")[-1]) + 1
            ticket_channel = await category.create_text_channel(f"ticket {ticket_num}", permission_synced=True)

            await ticket_channel.set_permissions(payload.member, read_messages=True, send_messages=True)

            message = await channel.fetch_message(msg_id)
            await message.remove_reaction(payload.emoji, payload.member)

            
            embed=discord.Embed(title="Ticket Opened",description=f"Support will be with you shortly. Use `!close` to close the ticket.",color=discord.Color.green())
            embed.set_footer(text="Made by lxy#5676")
            await ticket_channel.send(f"{payload.member.mention} Welcome", embed=embed)

            try:
                await client.wait_for("message", check=lambda m: m.channel == ticket_channel and m.content == "!close")
            
            except:
                pass

            else:
                time.sleep(.5)
                await ticket_channel.delete()

@client.command()
@commands.has_permissions(administrator=True)
async def setup(ctx,msg: discord.Message=None, category: discord.CategoryChannel=None):
    if msg is None or category is None:
        embed=discord.Embed(title="Ticket Error",description="Argument(s) was not given or was invalid.",color=discord.Color.red())
        embed.set_footer(text="Made by lxy#5676")
        await ctx.channel.send(embed=embed)
        return

    client.ticket_configs[ctx.guild.id] = [msg.id, msg.channel.id, category.id]

    async with aiofiles.open("ticket_configs.txt", mode="r") as file:
        data = await file.readlines()
    
    async with aiofiles.open("ticket_configs.txt", mode="w") as file:
        await file.write(f"{ctx.guild.id} {msg.id} {msg.channel.id} {category.id}\n")

        for line in data:
            if int(line.split(" ")[0]) != ctx.guild.id:
                await file.write(line)
                
    await msg.add_reaction(u"\U0001F3AB")

    embed=discord.Embed(title="Ticket Success",description="Ticket system successfully setup.",color=discord.Color.green())
    embed.set_footer(text="Made by lxy#5676")
    await ctx.channel.send(embed=embed)

@client.command()
@commands.has_permissions(administrator=True)
async def blacklist(ctx, user: discord.Member):
    if user == ctx.message.author:
        embed=discord.Embed(title="Blacklist Error",description="You can't blacklist yourself.",color=discord.Color.red())
        await ctx.send(embed=embed)
    else:
        try:
            client.blacklisted_users.append(user.id)
            data = read_json("blacklist")
            data["blacklistedUsers"].append(user.id)
            write_json(data, "blacklist")
            embed=discord.Embed(title="User Blacklisted!",description=f"{user.mention} Has Been Blacklisted.",color=discord.Color.green())
            embed.set_footer(text="Made by lxy#5676")
            await ctx.send(embed=embed)
        except:
            embed=discord.Embed(title="Blacklist Error",description="Can't find mentioned user.",color=discord.Color.red())
            embed.set_footer(text="Made by lxy#5676")
            await ctx.send(embed=embed)

@client.command()
@commands.has_permissions(administrator=True)
async def unblacklist(ctx, user: discord.Member):
    try:
        client.blacklisted_users.remove(user.id)
        data = read_json("blacklist")
        data["blacklistedUsers"].remove(user.id)
        write_json(data, "blacklist")
        embed=discord.Embed(title="User Unblacklisted!",description=f"{user.mention} Has Been Unblacklisted.",color=discord.Color.green())
        embed.set_footer(text="Made by lxy#5676")
        await ctx.send(embed=embed)
    except:
        embed=discord.Embed(title="Unblacklist Error",description="Mentioned user is not blacklisted.",color=discord.Color.red())
        embed.set_footer(text="Made by lxy#5676")
        await ctx.send(embed=embed)

client.run("")
