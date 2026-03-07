import discord
from discord.ext import commands
from discord import app_commands
import os

# ================================
# KONFIGURASI - Edit bagian ini!
# ================================

# Daftar role yang bisa dipilih
# Format: {"label": "Nama Role", "role_id": ID_ROLE, "emoji": "emoji", "description": "keterangan"}
ROLES = [
    {"label": "Pokemon Center", "role_id": 123456789, "emoji": "🎮", "description": "Pokemon fans"},
    {"label": "Genshin & Starrail", "role_id": 123456790, "emoji": "⚙️", "description": "Hoyoverse games"},
    {"label": "Kuroverse", "role_id": 123456791, "emoji": "🕊️", "description": "Wuthering Waves, Punishing Gray Raven"},
    {"label": "RPG", "role_id": 123456792, "emoji": "🎃", "description": "RPG games"},
    {"label": "Tri Holy Trinity", "role_id": 123456793, "emoji": "✨", "description": "FGO, Arknights, Blue Archive"},
    {"label": "Minecraft", "role_id": 123456794, "emoji": "⛏️", "description": "Minecraft players"},
    {"label": "Roblox", "role_id": 123456795, "emoji": "🍄", "description": "Roblox players"},
    {"label": "Football", "role_id": 123456796, "emoji": "⚽", "description": "EAFC, EFootball"},
    {"label": "Basketball", "role_id": 123456797, "emoji": "🏀", "description": "Basketball fans"},
]

# Channel ID tempat bot akan kirim pesan dropdown
CHANNEL_ID = 1479580316002943006  # Ganti dengan channel ID kamu

# Judul dan deskripsi embed
EMBED_TITLE = "🎮 Games Catalog"
EMBED_DESCRIPTION = "Silakan pilih roles sesuai dengan keinginan kamu untuk mengakses channel yang tersedia di bawah sini!"
EMBED_COLOR = 0x5865F2  # Warna biru Discord

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
            placeholder="🎮 Click menu ini untuk memilih roles!",
            min_values=1,
            max_values=len(options),  # Bisa pilih lebih dari 1
            options=options
        )
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        guild = interaction.guild
        member = interaction.user
        
        # Ambil semua role ID yang ada di ROLES config
        all_managed_role_ids = {str(r["role_id"]) for r in ROLES}
        
        # Role yang dipilih user
        selected_role_ids = set(self.values)
        
        added_roles = []
        removed_roles = []
        
        for role_data in ROLES:
            role_id = str(role_data["role_id"])
            role = guild.get_role(role_data["role_id"])
            
            if not role:
                continue
            
            if role_id in selected_role_ids:
                # Tambah role jika belum punya
                if role not in member.roles:
                    await member.add_roles(role)
                    added_roles.append(role_data["label"])
            else:
                # Hapus role jika sudah punya tapi tidak dipilih lagi
                if role in member.roles:
                    await member.remove_roles(role)
                    removed_roles.append(role_data["label"])
        
        # Buat response message
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
        super().__init__(timeout=None)  # Tidak timeout (persistent)
        self.add_item(RoleSelect())


# ================================
# BOT EVENTS & COMMANDS
# ================================

@bot.event
async def on_ready():
    print(f"✅ Bot {bot.user} sudah online!")
    
    # Register persistent view
    bot.add_view(RoleView())
    
    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} slash command(s)")
    except Exception as e:
        print(f"❌ Error syncing commands: {e}")


@bot.tree.command(name="setup_roles", description="Kirim pesan dropdown role ke channel")
@app_commands.checks.has_permissions(administrator=True)
async def setup_roles(interaction: discord.Interaction):
    """Command untuk admin kirim pesan dropdown"""
    
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        await interaction.response.send_message("❌ Channel tidak ditemukan! Cek CHANNEL_ID di config.", ephemeral=True)
        return
    
    # Buat embed
    embed = discord.Embed(
        title=EMBED_TITLE,
        description=EMBED_DESCRIPTION,
        color=EMBED_COLOR
    )
    
    # Tambah list games ke embed
    games_list = "\n".join([f"{r['emoji']} | **{r['label']}**" for r in ROLES])
    embed.add_field(name="📋 Available Roles", value=games_list, inline=False)
    embed.set_footer(text="Kamu bisa pilih lebih dari 1 role!")
    
    # Kirim ke channel
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

TOKEN = os.getenv("DISCORD_TOKEN")  # Ambil token dari environment variable

if not TOKEN:
    print("❌ ERROR: DISCORD_TOKEN tidak ditemukan!")
    print("Set environment variable DISCORD_TOKEN dengan token bot kamu.")
else:
    bot.run(TOKEN)