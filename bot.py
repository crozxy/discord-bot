import discord
from discord.ext import commands
from discord import app_commands
import os

# ================================
# KONFIGURASI - Edit bagian ini!
# ================================

ROLES = [
    {"label": "Pokemon Center", "role_id": 1479574417616011298, "emoji": "🎮", "description": "GTA Roleplay"},
    {"label": "Genshin & Starrail", "role_id": 1479574421680427200, "emoji": "⚙️", "description": "Mobile Legends"},
    {"label": "Kuroverse", "role_id": 1479574425102975200, "emoji": "🕊️", "description": "PUBG Mobile"},
    {"label": "RPG", "role_id": 1479574431293636752, "emoji": "🎃", "description": "Free Fire"},
    {"label": "Tri Holy Trinity", "role_id": 1479574873297780936, "emoji": "✨", "description": "Valorant"},
    {"label": "Minecraft", "role_id": 1479574876795965470, "emoji": "⛏️", "description": "Delta Force"},
    {"label": "Roblox", "role_id": 1479574879937232999, "emoji": "🍄", "description": "Fortnite"},
    {"label": "Football", "role_id": 1479574884152512626, "emoji": "⚽", "description": "Point Blank"},
    {"label": "Basketball", "role_id": 1479574887675727915, "emoji": "🏀", "description": "Ayodance"},
    {"label": "Basketball", "role_id": 1479575183093403802, "emoji": "🏀", "description": "Cs Online"},
    {"label": "Basketball", "role_id": 1479807001088491721, "emoji": "🏀", "description": "Roblox"},
]

# Ganti dengan Channel ID kamu
CHANNEL_ID = 1479580316002943006

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
# DROPDOWN VIEW
# ================================

class RoleSelect(discord.ui.Select):
    def __init__(self):
        options = []
        for role_data in ROLES:
            options.append(
                discord.SelectOption(
                    label=role_data["label"],
                    value=str(role_data["role_id"]),
                    emoji=role_data["emoji"],
                    description=role_data.get("description", "")
                )
            )

        super().__init__(
            custom_id="role_select_menu",  # WAJIB untuk persistent view
            placeholder="🎮 Click menu ini untuk memilih roles!",
            min_values=1,
            max_values=len(options),
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild
        member = interaction.user
        selected_role_ids = set(self.values)

        added_roles = []
        removed_roles = []

        for role_data in ROLES:
            role_id = str(role_data["role_id"])
            role = guild.get_role(role_data["role_id"])

            if not role:
                continue

            if role_id in selected_role_ids:
                if role not in member.roles:
                    await member.add_roles(role)
                    added_roles.append(role_data["label"])
            else:
                if role in member.roles:
                    await member.remove_roles(role)
                    removed_roles.append(role_data["label"])

        msg = ""
        if added_roles:
            msg += f"✅ **Role ditambahkan:** {', '.join(added_roles)}\n"
        if removed_roles:
            msg += f"❌ **Role dihapus:** {', '.join(removed_roles)}\n"
        if not added_roles and not removed_roles:
            msg = "ℹ️ Tidak ada perubahan role."

        await interaction.followup.send(msg, ephemeral=True)


class RoleView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(RoleSelect())


# ================================
# BOT EVENTS & COMMANDS
# ================================

@bot.event
async def on_ready():
    print(f"✅ Bot {bot.user} sudah online!")
    bot.add_view(RoleView())
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} slash command(s)")
    except Exception as e:
        print(f"❌ Error syncing commands: {e}")


@bot.tree.command(name="setup_roles", description="Kirim pesan dropdown role ke channel")
@app_commands.checks.has_permissions(administrator=True)
async def setup_roles(interaction: discord.Interaction):
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        await interaction.response.send_message("❌ Channel tidak ditemukan! Cek CHANNEL_ID di config.", ephemeral=True)
        return

    embed = discord.Embed(title=EMBED_TITLE, description=EMBED_DESCRIPTION, color=EMBED_COLOR)
    games_list = "\n".join([f"{r['emoji']} | **{r['label']}**" for r in ROLES])
    embed.add_field(name="📋 Available Roles", value=games_list, inline=False)
    embed.set_footer(text="Kamu bisa pilih lebih dari 1 role!")

    await channel.send(embed=embed, view=RoleView())
    await interaction.response.send_message(f"✅ Berhasil kirim dropdown ke {channel.mention}!", ephemeral=True)


@bot.tree.command(name="my_roles", description="Lihat role yang kamu punya")
async def my_roles(interaction: discord.Interaction):
    member = interaction.user
    managed_role_ids = {r["role_id"] for r in ROLES}
    user_game_roles = [r for r in member.roles if r.id in managed_role_ids]

    if user_game_roles:
        role_names = ", ".join([r.name for r in user_game_roles])
        await interaction.response.send_message(f"🎮 Role kamu: **{role_names}**", ephemeral=True)
    else:
        await interaction.response.send_message("ℹ️ Kamu belum memilih role apapun.", ephemeral=True)


# ================================
# RUN BOT
# ================================

TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    print("❌ ERROR: DISCORD_TOKEN tidak ditemukan!")
else:
    bot.run(TOKEN)
