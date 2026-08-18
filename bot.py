from flask import Flask
from threading import Thread
import os
import discord
from discord.ext import commands
from discord import app_commands

# ================================
# SETUP FLASK UNTUK KEEP-ALIVE
# ================================

app = Flask('')

@app.route('/')
def home():
    return "Bot Discord Online!"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

keep_alive()

# ================================
# BOT SETUP
# ================================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ================================
# DROPDOWN VIEW (DINAMIS & PERSISTENT)
# ================================

class RoleSelect(discord.ui.Select):
    def __init__(self, roles_data):
        options = []
        for role_data in roles_data:
            options.append(
                discord.SelectOption(
                    label=role_data["label"],
                    value=str(role_data["role_id"]),
                    emoji=role_data.get("emoji", "🎮")
                )
            )

        super().__init__(
            custom_id="role_select_menu",  # Wajib untuk Persistent View
            placeholder="🎮 Click menu ini untuk memilih roles!",
            min_values=0,
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

        # Ambil semua role ID yang ada di dalam menu dropdown ini
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
            msg += f"✅ **Role ditambahkan:** {', '.join(added_roles)}\n"
        if removed_roles:
            msg += f"❌ **Role dihapus:** {', '.join(removed_roles)}\n"
        if not added_roles and not removed_roles:
            msg = "ℹ️ Tidak ada perubahan role."

        await interaction.followup.send(msg, ephemeral=True)


class RoleView(discord.ui.View):
    def __init__(self, roles_data=None):
        super().__init__(timeout=None)
        if roles_data:
            self.add_item(RoleSelect(roles_data))


# ================================
# BOT EVENTS & COMMANDS
# ================================

@bot.event
async def on_ready():
    print(f"✅ Bot {bot.user} sudah online!")
    
    # Sync Slash Commands secara Global ke semua server
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} slash command(s) secara global!")
    except Exception as e:
        print(f"❌ Error syncing commands: {e}")


@bot.tree.command(name="setup_roles", description="Kirim pesan dropdown role di channel saat ini")
@app_commands.checks.has_permissions(administrator=True)
async def setup_roles(interaction: discord.Interaction):
    """
    Perintah ini akan mengambil SEMUA role yang ada di server tempat kamu mengetikkan command,
    lalu membuatnya menjadi menu dropdown secara otomatis!
    """
    guild = interaction.guild
    
    # Ambil role server (mengabaikan role @everyone dan role bot)
    roles = [r for r in guild.roles if not r.is_default() and not r.is_integration() and not r.managed]
    
    if not roles:
        await interaction.response.send_message("❌ Tidak ada role yang bisa ditampilkan di server ini!", ephemeral=True)
        return

    # Batasi maksimal 25 role per dropdown (limit bawaan Discord UI)
    roles = roles[:25]
    roles_data = [{"label": r.name, "role_id": r.id, "emoji": "🎮"} for r in roles]

    embed = discord.Embed(
        title="🎮 Games Catalog / Select Roles",
        description="Silakan pilih roles sesuai dengan keinginan kamu untuk mengakses channel yang tersedia!",
        color=0x5865F2
    )
    
    games_list = "\n".join([f"🎮 | **{r.name}**" for r in roles])
    embed.add_field(name="📋 Available Roles", value=games_list, inline=False)
    embed.set_footer(text="Kamu bisa pilih lebih dari 1 role!")

    view = RoleView(roles_data)
    
    # Kirim langsung ke channel tempat command dipanggil
    await interaction.channel.send(embed=embed, view=view)
    await interaction.response.send_message(f"✅ Berhasil mengirim dropdown role ke channel {interaction.channel.mention}!", ephemeral=True)


@bot.tree.command(name="my_roles", description="Lihat role yang kamu punya")
async def my_roles(interaction: discord.Interaction):
    member = interaction.user
    roles = [r.name for r in member.roles if not r.is_default()]

    if roles:
        role_names = ", ".join(roles)
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
