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
# BOT SETUP
# ================================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ================================
# DROPDOWN ROLE SELECTION
# ================================

class GameRoleSelect(discord.ui.Select):
    def __init__(self, roles_data):
        options = []
        for role_data in roles_data:
            options.append(
                discord.SelectOption(
                    label=role_data["name"],
                    value=str(role_data["id"]),
                    emoji="🎮",
                    description=f"Pilih untuk mengambil role {role_data['name']}"
                )
            )

        super().__init__(
            custom_id="game_role_select_menu",
            placeholder="🎮 Click menu ini untuk memilih roles!",
            min_values=0,            # Boleh kosongkan semua
            max_values=len(options),  # Bisa pilih LEBIH DARI 1 role sekaligus
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild
        member = interaction.user
        selected_role_ids = set(self.values)

        added_roles = []
        removed_roles = []

        all_option_role_ids = {int(opt.value) for opt in self.options}

        for role_id in all_option_role_ids:
            role = guild.get_role(role_id)
            if not role:
                continue

            if str(role_id) in selected_role_ids:
                if role not in member.roles:
                    await member.add_roles(role)
                    added_roles.append(role.name)
            else:
                if role in member.roles:
                    await member.remove_roles(role)
                    removed_roles.append(role.name)

        msg = ""
        if added_roles:
            msg += f"✅ **Role game ditambahkan:** {', '.join(added_roles)}\n"
        if removed_roles:
            msg += f"❌ **Role game dilepas:** {', '.join(removed_roles)}\n"
        if not added_roles and not removed_roles:
            msg = "ℹ️ Tidak ada perubahan pada role game kamu."

        await interaction.followup.send(msg, ephemeral=True)


class GameRoleView(discord.ui.View):
    def __init__(self, roles_data):
        super().__init__(timeout=None)
        self.add_item(GameRoleSelect(roles_data))


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

    # Mencocokkan daftar GAME_LIST dengan Role yang ada di Server Settings Discord
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

    # Buat Tampilan Embed Persis Seperti di Gambar
    embed = discord.Embed(
        title=EMBED_TITLE,
        description=EMBED_DESCRIPTION,
        color=EMBED_COLOR
    )
    
    games_list_str = "\n".join([f"🎮 | **{r['name']}**" for r in found_roles])
    embed.add_field(name="📋 Available Roles", value=games_list_str, inline=False)
    embed.set_footer(text="Kamu bisa pilih lebih dari 1 role!")

    # Kirim Embed + Dropdown
    await interaction.response.send_message(embed=embed, view=GameRoleView(found_roles))

    # Peringatan rahasia untuk Admin jika ada role yang belum sempat dibuat
    if missing_roles:
        await interaction.followup.send(
            f"⚠️ **Info Admin:** Role berikut belum ditemukan di Server Settings: `{', '.join(missing_roles)}`",
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
