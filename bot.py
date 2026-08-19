from flask import Flask
from threading import Thread
import os
import discord
from discord.ext import commands
from discord import app_commands

# ================================
# KEEP ALIVE SERVER (FLASK)
# ================================

app = Flask('')

@app.route('/')
def home():
    return "Bot Role Game Online!"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

keep_alive()

# ================================
# MAPPING GAME & CUSTOM EMOJI
# ================================

GAME_EMOJIS = {
    "Roblox": {"name": "roblox", "id": 1539595113288831006},
    "GTA Roleplay": {"name": "gtaroleplay", "id": 1539596445026484244},
    "Mobile Legends": {"name": "mobilelegends", "id": 1539596724039983205},
    "PUBG Mobile": {"name": "pubgmobile", "id": 1539596200481661008},
    "PUBG PC": {"name": "pubgpc", "id": 1539597049866231838},
    "Free Fire": {"name": "freefire", "id": 1539597493397102694},
    "Valorant": {"name": "valorant", "id": 1539594228819165244},
    "Delta Force": {"name": "deltaforce", "id": 1539598339996258436},
    "Fortnite": {"name": "fortnite", "id": 1539598447869427814},
    "Point Blank": {"name": "pointblank", "id": 1539598575535788092},
    "Ayodance": {"name": "ayodance", "id": 1539598709237481553},
    "CS Online": {"name": "csonline", "id": 1539599086632570950},
    "Game Lain": {"name": "gamelain", "id": 1539599212273205248}
}

GAME_LIST = list(GAME_EMOJIS.keys())

EMBED_TITLE = "🎮 Games Catalog"
EMBED_DESCRIPTION = "Silakan pilih roles sesuai dengan keinginan kamu untuk mengakses channel yang tersedia di bawah sini!"
EMBED_COLOR = 0x5865F2

# Helper function untuk format string emoji di Embed
def get_emoji_str(game_name):
    data = GAME_EMOJIS.get(game_name)
    if data:
        return f"<:{data['name']}:{data['id']}>"
    return "🎮"

# Helper function untuk objek PartialEmoji di Select Option Dropdown
def get_partial_emoji(game_name):
    data = GAME_EMOJIS.get(game_name)
    if data:
        return discord.PartialEmoji(name=data["name"], id=data["id"])
    return discord.PartialEmoji(name="🎮")


# ================================
# DROPDOWN SELECTION (PERSISTENT)
# ================================

class DynamicRoleSelect(discord.ui.Select):
    def __init__(self):
        options = [discord.SelectOption(label="Loading...", value="0")]
        super().__init__(
            custom_id="persistent_game_role_select",
            placeholder="🎮 Click menu ini untuk memilih roles!",
            min_values=0,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild
        member = interaction.user

        game_roles = [r for r in guild.roles if r.name in GAME_LIST]
        selected_role_ids = {int(val) for val in self.values if val.isdigit()}

        added_roles = []
        removed_roles = []

        for role in game_roles:
            if role.id in selected_role_ids:
                if role not in member.roles:
                    try:
                        await member.add_roles(role)
                        added_roles.append(f"{get_emoji_str(role.name)} **{role.name}**")
                    except discord.Forbidden:
                        pass
            else:
                if role in member.roles:
                    try:
                        await member.remove_roles(role)
                        removed_roles.append(f"{get_emoji_str(role.name)} **{role.name}**")
                    except discord.Forbidden:
                        pass

        msg = ""
        if added_roles:
            msg += f"✅ **Role game ditambahkan:** {', '.join(added_roles)}\n"
        if removed_roles:
            msg += f"❌ **Role game dilepas:** {', '.join(removed_roles)}\n"
        if not added_roles and not removed_roles:
            msg = "ℹ️ Tidak ada perubahan pada role game kamu."

        await interaction.followup.send(msg, ephemeral=True)


class GameRoleView(discord.ui.View):
    def __init__(self, roles_data=None):
        super().__init__(timeout=None)
        
        if roles_data:
            self.clear_items()
            select = discord.ui.Select(
                custom_id="persistent_game_role_select",
                placeholder="🎮 Click menu ini untuk memilih roles!",
                min_values=0,
                max_values=len(roles_data),
                options=[
                    discord.SelectOption(
                        label=r["name"],
                        value=str(r["id"]),
                        emoji=get_partial_emoji(r["name"])
                    ) for r in roles_data
                ]
            )
            select.callback = DynamicRoleSelect().callback
            self.add_item(select)
        else:
            self.clear_items()
            self.add_item(DynamicRoleSelect())


# ================================
# BOT CLASS WITH SETUP HOOK
# ================================

class RoleBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        self.add_view(GameRoleView())


bot = RoleBot()

# ================================
# EVENTS & COMMANDS
# ================================

@bot.event
async def on_ready():
    print(f"✅ Bot {bot.user} sudah aktif!")
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} slash command(s) secara global!")
    except Exception as e:
        print(f"❌ Gagal sync command: {e}")


@bot.tree.command(name="setup_roles", description="Kirim menu dropdown catalog game di channel saat ini")
@app_commands.checks.has_permissions(administrator=True)
async def setup_roles(interaction: discord.Interaction):
    guild = interaction.guild

    found_roles = []
    missing_roles = []

    for game_name in GAME_LIST:
        role = discord.utils.get(guild.roles, name=game_name)
        if role:
            found_roles.append({"name": role.name, "id": role.id})
        else:
            missing_roles.append(game_name)

    if not found_roles:
        await interaction.response.send_message(
            "❌ Belum ada role game yang dibuat di Server Settings! Buat role seperti Roblox, Mobile Legends, dll terlebih dahulu.",
            ephemeral=True
        )
        return

    embed = discord.Embed(
        title=EMBED_TITLE,
        description=EMBED_DESCRIPTION,
        color=EMBED_COLOR
    )
    
    games_list_str = "\n".join([f"{get_emoji_str(r['name'])} | **{r['name']}**" for r in found_roles])
    embed.add_field(name="📋 Available Roles", value=games_list_str, inline=False)
    embed.set_footer(text="Kamu bisa pilih lebih dari 1 role!")

    await interaction.response.send_message(embed=embed, view=GameRoleView(found_roles))

    if missing_roles:
        await interaction.followup.send(
            f"⚠️ **Info Admin:** Role berikut belum dibuat di Server Settings: `{', '.join(missing_roles)}`",
            ephemeral=True
        )


# ================================
# RUN BOT
# ================================

TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    print("❌ ERROR: DISCORD_TOKEN tidak ditemukan!")
else:
    bot.run(TOKEN)
