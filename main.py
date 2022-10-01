from typing import Optional

import dnd
import discord
import os
from discord.ext import commands
from discord import app_commands

intents = discord.Intents.default()
bot = commands.Bot(intents=intents, command_prefix=".")
# TOKEN = ''
f = open('bot_token.txt')
TOKEN = f.read()
f.close()

BOBBY_ID = 372447300586569730

def getCustomData(character, itemNum):
    characterValues = character['characterValues']
    customData = []
    for i in characterValues:
        if int(i['valueId']) == character['inventory'][itemNum]['id'] and int(i['valueTypeId']) == character['inventory'][itemNum]['entityTypeId']:
            customData.append(i)
    
    return customData

class ConfirmGive(discord.ui.View):
    def __init__(self, inventory, values, characterTo, characterFrom):
        super().__init__()
        self.value = None
        self.inventory = inventory
        self.characterFrom = characterFrom
        self.characterTo = characterTo
        self.values = values

    # When the confirm button is pressed, set the inner value to `True` and
    # stop the View from listening to more input.
    # We also send the user an ephemeral message that we're confirming their choice.
    @discord.ui.button(label='Confirm', style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        itemNum = int(self.values[0])
        await interaction.response.edit_message(content=f"Sending **{self.inventory[itemNum]['definition']['name']}** to **{self.characterTo['name']}**...", view=None)
        

        success = dnd.give(self.characterFrom["id"], self.characterTo["id"], self.inventory[itemNum], 1, getCustomData(self.characterFrom, itemNum))

        original_message = await interaction.original_response()
        if success:
            await original_message.edit(content=f"You gave your **{self.inventory[itemNum]['definition']['name']}** to **{self.characterTo['name']}**", view=None)
            bob = await bot.fetch_user(BOBBY_ID)
            await bob.send(f"**{self.characterFrom['name']}** sent their *{self.inventory[itemNum]['definition']['name']}* to **{self.characterTo['name']}**")
        else:
            await original_message.edit(content="Something went wrong! Do you still have the item?", view=None)
        
        self.value = True
        self.stop()

    # This one is similar to the confirmation button except sets the inner value to `False`
    @discord.ui.button(label='Cancel', style=discord.ButtonStyle.grey)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content=f"Cancelled.", view=None)
        self.value = False
        self.stop()

class ConfirmPay(discord.ui.View):
    def __init__(self, characterTo, characterFromId, amount_str, cp=0, sp=0, ep=0, gp=0, pp=0):
        super().__init__()
        self.value = None
        self.characterTo = characterTo
        self.characterFromId = characterFromId
        self.amount_str = amount_str
        self.cp = cp
        self.sp = sp
        self.ep = ep
        self.gp = gp
        self.pp = pp

    # When the confirm button is pressed, set the inner value to `True` and
    # stop the View from listening to more input.
    # We also send the user an ephemeral message that we're confirming their choice.
    @discord.ui.button(label='Confirm', style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content=f"Sending {self.amount_str} to **{self.characterTo['name']}**...", view=None)
        

        success = dnd.pay(self.characterFromId, self.characterTo['id'], self.cp, self.sp, self.ep, self.gp, self.pp)

        original_message = await interaction.original_response()
        if success == False:
            await original_message.edit(content=f"Something went wrong! Do you have enough balance? You might be a broke bitch", view=None)
        else:
            await original_message.edit(content=f"You paid **{self.characterTo['name']}** {self.amount_str}", view=None)
            characterFrom = dnd.get_character(self.characterFromId)
            bob = await bot.fetch_user(BOBBY_ID)
            await bob.send(f"**{characterFrom['name']}** paid **{self.characterTo['name']}** {self.amount_str}")
        self.stop()

    # This one is similar to the confirmation button except sets the inner value to `False`
    @discord.ui.button(label='Cancel', style=discord.ButtonStyle.grey)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content=f"Cancelled.", view=None)
        self.value = False
        self.stop()

class Dropdown(discord.ui.Select):
    def __init__(self, characterFrom, dndCharIdTo):
        self.dndCharIdTo = dndCharIdTo
        self.characterFrom = characterFrom
        self.inventory = characterFrom['inventory']
        options = []
        for n, item in enumerate(self.inventory):
            options.append(
                discord.SelectOption(
                    label=item['definition']['name'],
                    value=n,
                    description=item['definition']['filterType'] + ", " + item['definition']['rarity']
                )
            )

        super().__init__(placeholder="pick something", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        characterTo = dnd.get_character(self.dndCharIdTo)
        view = ConfirmGive(self.inventory, self.values, characterTo, self.characterFrom)
        await interaction.response.edit_message(content=f"Are you sure you want to give your **{self.inventory[int(self.values[0])]['definition']['name']}** to *{characterTo['name']}*?", view=view)

        await view.wait()

class DropdownView(discord.ui.View):
    def __init__(self, character, dndCharIdTo):
        super().__init__()
        self.add_item(Dropdown(character, dndCharIdTo))

def get_dnd_from_discord(discordId):
    f = open('characters.txt')
    all = eval(f.read())
    f.close()
    if discordId in all:
        return all[discordId]
    return False

@bot.event
async def on_ready():
    await bot.tree.sync()
    print("Logged in!")

@bot.tree.command(description="Give an item from your inventory to another player")
async def give(interaction: discord.Interaction, player: discord.Member):
    dndCharIdFrom = get_dnd_from_discord(interaction.user.id)
    characterFrom = dnd.get_character(dndCharIdFrom)

    dndCharIdTo = get_dnd_from_discord(player.id)
    if dndCharIdTo == False:
        await interaction.response.send_message(content=f"{player.display_name} is not part of the campaign retard", ephemeral=True)
        return
    characterTo = dnd.get_character(dndCharIdTo)
    await interaction.response.send_message(content=f"What do you want to give to {characterTo['name']}?", ephemeral=True, view=DropdownView(characterFrom, dndCharIdTo))

@bot.tree.command(description="Pay another player various currencies")
@app_commands.describe(cp='Copper')
@app_commands.describe(sp='Silver')
@app_commands.describe(ep='Electrum')
@app_commands.describe(gp='Gold')
@app_commands.describe(pp='Platinum')
async def pay(
    interaction: discord.Interaction, 
    player: discord.Member, 
    cp: Optional[app_commands.Range[int, 0, None]] = 0, 
    sp: Optional[app_commands.Range[int, 0, None]] = 0, 
    ep: Optional[app_commands.Range[int, 0, None]] = 0, 
    gp: Optional[app_commands.Range[int, 0, None]] = 0, 
    pp: Optional[app_commands.Range[int, 0, None]] = 0
):
    dndCharIdFrom = get_dnd_from_discord(interaction.user.id)
    dndCharIdTo = get_dnd_from_discord(player.id)
    if dndCharIdTo == False:
        await interaction.response.send_message(content=f"{player.display_name} is not part of the campaign retard", ephemeral=True)
        return
    characterTo = dnd.get_character(dndCharIdTo)

    amounts = {'copper': cp, 'silver': sp, 'electrum': ep, 'gold': gp, 'platinum': pp}
    amount_str = ""
    for i in amounts:
        if amounts[i] > 0:
            amount_str += str(amounts[i]) + f" {i}, "
    if len(amount_str) == 0:
        await interaction.response.send_message(content="You need to include some value to send moron", ephemeral=True)
        return
    
    amount_str = amount_str[0:len(amount_str)-2]

    view = ConfirmPay(characterTo, dndCharIdFrom, amount_str, cp, sp, ep, gp, pp)
    await interaction.response.send_message(content=f"Are you sure you want to pay **{characterTo['name']}** {amount_str}?", view=view, ephemeral=True)

    await view.wait()

def check_if_bob(interaction: discord.Interaction) -> bool:
    return interaction.user.id == BOBBY_ID

@bot.tree.command(description="Only for DM")
@app_commands.check(check_if_bob)
async def login(interaction: discord.Interaction, cobalt_session: str):
    f = open("session.txt", "w")
    f.seek(0)
    f.truncate()
    f.write(cobalt_session)
    f.close()
    dnd.COBALT_SESSION = cobalt_session

    await interaction.response.send_message(content="Login info updated", ephemeral=True)



bot.run(TOKEN)
