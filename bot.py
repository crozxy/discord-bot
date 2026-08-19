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
# TEMPLATE DAFTAR GAME PERMANEN
# ================================

GAME_LIST = [
    "Roblox",
    "GTA Roleplay",
    "Mobile Legends",
    "PUBG Mobile",
    "PUBG PC",
    "Free Fire",
    "Valorant",
    "Delta Force",
    "Fortnite",
    "Point Blank",
    "Ayodance",
    "CS Online",
    "Game Lain"
]

EMBED_TITLE = "🎮 Games Catalog"
EMBED_DESCRIPTION = "Silakan pilih roles sesuai dengan keinginan kamu untuk mengakses channel yang tersedia di bawah sini!"
EMBED_COLOR = 0x5865F2

# ================================
# DROPDOWN SELECTION (PERSISTENT)
# ================================

class DynamicRoleSelect(discord.ui.Select):
    def __init__(self):
        # Placeholder awal sebelum diisi opsi role aktual
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

        # Dapatkan semua role game yang cocok di server saat ini
        game_roles = [r for r in guild.roles if r.name in GAME_LIST]
        game_role_ids = {r.id for r in game_roles}

        selected_role_ids = {int(val) for val in self.values if val.isdigit()}

        added_roles = []
        removed_roles = []

        for role in game_roles:
            if role.id in selected_role_ids:
                if role not in member.roles:
                    try:
                        await member.add_roles(role)
                        added_roles.append(role.name)
                    except discord.Forbidden:
                        pass
            else:
                if role in member.roles:
                    try:
                        await member.remove_roles(role)
                        removed_roles.append(role.name)
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
            # Mengisi opsi dropdown saat command /setup_roles dijalankan
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
                        emoji="🎮"
                    ) for r in roles_data
                ]
            )
            select.callback = DynamicRoleSelect().callback
            self.add_item(select)
        else:
            # Default persistent listener saat bot restart
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
        # Mendaftarkan Persistent View agar interaksi tetap aktif setelah restart
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
    
    games_list_str = "\n".join([f"🎮 | **{r['name']}**" for r in found_roles])
    embed.add_field(name="📋 Available Roles", value=games_list_str, inline=False)
    embed.set_footer(text="Kamu bisa pilih lebih dari 1 role!")

    # Kirim Embed + View dengan Custom ID Persisten
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
