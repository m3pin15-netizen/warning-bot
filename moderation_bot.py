"""
بوت ديسكورد للمودريشن (Moderation Bot)
يحتاج: pip install -U discord.py

الأوامر المتاحة (Slash Commands):
- /kick @user [سبب]      -> طرد عضو
- /ban @user [سبب]       -> حظر عضو
- /unban user_id         -> فك حظر عضو
- /mute @user دقايق [سبب] -> كتم عضو (timeout)
- /unmute @user          -> فك كتم عضو
- /clear عدد             -> مسح رسايل
- /warn @user سبب        -> تحذير عضو (بيتسجل في الذاكرة، مش دائم)
- /warnings @user        -> عرض تحذيرات عضو

ملاحظة مهمة:
استخدم البوت ده بس في السيرفرات اللي انت أدمن فيها أو عندك إذن رسمي تديره.
"""

import discord
from discord import app_commands
from discord.ext import commands
import os

# ----------- الإعدادات -----------
TOKEN = os.getenv("DISCORD_BOT_TOKEN", "ضع_التوكن_بتاعك_هنا")

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# تخزين التحذيرات مؤقتًا في الذاكرة {guild_id: {user_id: [أسباب]}}
warnings_db: dict[int, dict[int, list[str]]] = {}


@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"تم تسجيل {len(synced)} أمر Slash")
    except Exception as e:
        print(f"خطأ في مزامنة الأوامر: {e}")
    print(f"البوت شغال باسم: {bot.user}")


def is_mod():
    """يتأكد إن اللي بيستخدم الأمر عنده صلاحية إدارة الأعضاء."""
    async def predicate(interaction: discord.Interaction) -> bool:
        return interaction.user.guild_permissions.manage_guild
    return app_commands.check(predicate)


# ----------- Kick -----------
@bot.tree.command(name="kick", description="طرد عضو من السيرفر")
@app_commands.describe(member="العضو اللي هيتطرد", reason="سبب الطرد")
@is_mod()
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "مفيش سبب محدد"):
    await member.kick(reason=reason)
    await interaction.response.send_message(f"✅ تم طرد {member.mention} | السبب: {reason}")


# ----------- Ban -----------
@bot.tree.command(name="ban", description="حظر عضو من السيرفر")
@app_commands.describe(member="العضو اللي هيتحظر", reason="سبب الحظر")
@is_mod()
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "مفيش سبب محدد"):
    await member.ban(reason=reason)
    await interaction.response.send_message(f"🔨 تم حظر {member.mention} | السبب: {reason}")


# ----------- Unban -----------
@bot.tree.command(name="unban", description="فك حظر عضو باستخدام الـ ID بتاعه")
@app_commands.describe(user_id="ايدي العضو")
@is_mod()
async def unban(interaction: discord.Interaction, user_id: str):
    try:
        user = await bot.fetch_user(int(user_id))
        await interaction.guild.unban(user)
        await interaction.response.send_message(f"✅ تم فك حظر {user.mention}")
    except Exception as e:
        await interaction.response.send_message(f"❌ حصل خطأ: {e}", ephemeral=True)


# ----------- Mute (Timeout) -----------
@bot.tree.command(name="mute", description="كتم عضو لمدة معينة بالدقايق")
@app_commands.describe(member="العضو", minutes="عدد الدقايق", reason="السبب")
@is_mod()
async def mute(interaction: discord.Interaction, member: discord.Member, minutes: int, reason: str = "مفيش سبب محدد"):
    duration = discord.utils.utcnow() + discord.timedelta(minutes=minutes)
    await member.timeout(duration, reason=reason)
    await interaction.response.send_message(f"🔇 تم كتم {member.mention} لمدة {minutes} دقيقة | السبب: {reason}")


# ----------- Unmute -----------
@bot.tree.command(name="unmute", description="فك كتم عضو")
@app_commands.describe(member="العضو")
@is_mod()
async def unmute(interaction: discord.Interaction, member: discord.Member):
    await member.timeout(None)
    await interaction.response.send_message(f"🔊 تم فك كتم {member.mention}")


# ----------- Clear Messages -----------
@bot.tree.command(name="clear", description="مسح عدد معين من الرسايل")
@app_commands.describe(amount="عدد الرسايل اللي هتتمسح")
@is_mod()
async def clear(interaction: discord.Interaction, amount: int):
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=amount)
    await interaction.followup.send(f"🧹 تم مسح {len(deleted)} رسالة", ephemeral=True)


# ----------- Warn -----------
@bot.tree.command(name="warn", description="إدي عضو تحذير")
@app_commands.describe(member="العضو", reason="سبب التحذير")
@is_mod()
async def warn(interaction: discord.Interaction, member: discord.Member, reason: str):
    guild_id = interaction.guild.id
    warnings_db.setdefault(guild_id, {}).setdefault(member.id, []).append(reason)
    count = len(warnings_db[guild_id][member.id])
    await interaction.response.send_message(f"⚠️ تم تحذير {member.mention} (تحذير رقم {count}) | السبب: {reason}")


# ----------- عرض التحذيرات -----------
@bot.tree.command(name="warnings", description="عرض تحذيرات عضو")
@app_commands.describe(member="العضو")
@is_mod()
async def warnings_cmd(interaction: discord.Interaction, member: discord.Member):
    guild_id = interaction.guild.id
    user_warnings = warnings_db.get(guild_id, {}).get(member.id, [])
    if not user_warnings:
        await interaction.response.send_message(f"{member.mention} مفيهوش أي تحذيرات ✅")
        return
    text = "\n".join(f"{i+1}. {w}" for i, w in enumerate(user_warnings))
    await interaction.response.send_message(f"تحذيرات {member.mention}:\n{text}")


# ----------- التعامل مع الأخطاء (زي عدم وجود صلاحية) -----------
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message("❌ معندكش صلاحية تستخدم الأمر ده.", ephemeral=True)
    else:
        await interaction.response.send_message(f"❌ حصل خطأ: {error}", ephemeral=True)


if __name__ == "__main__":
    bot.run(TOKEN)
