import discord
from discord.ext import commands
import random
import datetime

# Replace with your data:
TOKEN = ""

# Channels for family registration
INPUT_CHANNEL_ID = 12345    # Channel for family registration
REVIEW_CHANNEL_ID = 12345   # Channel for reviewing family registration applications
LOG_CHANNEL_ID = 12345      # Channel for logging family registration applications

# Channels for role issuance requests
ROLE_REQUEST_INPUT_CHANNEL_ID = 12345   # Channel to initiate a role issuance request
ROLE_REQUEST_REVIEW_CHANNEL_ID = 12345  # Channel for reviewing role issuance requests
ROLE_REQUEST_LOG_CHANNEL_ID = 12345     # Channel for logging role issuances

# Channels for suggestions and bug reports
SUGGESTION_CHANNEL_ID = 12345  # Channel where improvement suggestions are sent
BUG_REPORT_CHANNEL_ID = 12345  # Channel where bug reports are sent
BUG = 12345  # Channel for embeds with bug button
PREDOLOJ = 12345  # Channel for embeds with suggestion button

# Additional constants:
ALERT_ROLE_ID = 12345
BASE_ASSIGNABLE_ROLE_ID = 12345  # Filter: only roles below this one can be selected
ALLOWED_REQUEST_ROLE_ID = 12345  # Role that grants permission to use the role issuance system

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# ============================
#     FORM: Family Registration
# ============================
class FamilyModal(discord.ui.Modal, title="Family Registration"):
    family_name = discord.ui.TextInput(
        label="Family Name (without 'Family' suffix)",
        placeholder="Enter the family name",
        style=discord.TextStyle.short,
        max_length=50
    )
    creation_date = discord.ui.TextInput(
        label="Family Creation Date",
        placeholder="Enter the family creation date",
        style=discord.TextStyle.short,
        max_length=50
    )
    family_logo = discord.ui.TextInput(
        label="Family Logo [Imgur]",
        placeholder="Enter the URL of the logo (Imgur)",
        style=discord.TextStyle.short,
        max_length=200
    )
    family_mansion = discord.ui.TextInput(
        label="Family Mansion [Imgur] (if none, enter '-')",
        placeholder="Enter the URL of the mansion (Imgur) or '-'",
        style=discord.TextStyle.short,
        max_length=200
    )
    async def on_submit(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="✨ New Family Registration Application ✨",
            color=discord.Color.blurple(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name="Family Name", value=self.family_name.value, inline=False)
        embed.add_field(name="Family Creation Date", value=self.creation_date.value, inline=False)
        embed.add_field(name="Family Logo", value=self.family_logo.value, inline=False)
        embed.add_field(name="Family Mansion", value=self.family_mansion.value, inline=False)
        embed.set_footer(
            text=f"Application from {interaction.user}",
            icon_url=(interaction.user.avatar.url if interaction.user.avatar else None)
        )
        if self.family_logo.value.startswith("http"):
            embed.set_thumbnail(url=self.family_logo.value)
        review_channel = interaction.guild.get_channel(REVIEW_CHANNEL_ID)
        if review_channel is None:
            await interaction.response.send_message("❌ Error: review channel not found.", ephemeral=True)
            return
        view = ReviewView(
            submitter_id=interaction.user.id,
            family_name=self.family_name.value,
            creation_date=self.creation_date.value,
            family_logo=self.family_logo.value,
            family_mansion=self.family_mansion.value
        )
        mention_text = f"<@&{ALERT_ROLE_ID}>"
        sent_message = await review_channel.send(content=mention_text, embed=embed, view=view)
        view.message = sent_message
        await interaction.response.send_message("✅ Your application has been sent for review.", ephemeral=True)

class ReviewView(discord.ui.View):
    def __init__(self, submitter_id: int, family_name: str, creation_date: str, family_logo: str, family_mansion: str):
        super().__init__(timeout=None)
        self.submitter_id = submitter_id
        self.family_name = family_name
        self.creation_date = creation_date
        self.family_logo = family_logo
        self.family_mansion = family_mansion
        self.message: discord.Message = None
    @discord.ui.button(label="✅ Approve", style=discord.ButtonStyle.success, custom_id="family_approve")
    async def approve_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Only administrators can approve applications.", ephemeral=True)
            return
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message("❌ Error: server not found.", ephemeral=True)
            return
        submitter = guild.get_member(self.submitter_id)
        if submitter is None:
            await interaction.response.send_message("❌ Error: application author not found.", ephemeral=True)
            return
        role_name = f"{self.family_name}Family"
        random_color = discord.Color(random.randint(0, 0xFFFFFF))
        try:
            role = await guild.create_role(name=role_name, color=random_color, reason="Family Registration")
        except Exception as e:
            await interaction.response.send_message(f"❌ Error creating role: {e}", ephemeral=True)
            return
        try:
            dm_embed = discord.Embed(
                title="Your application has been approved!",
                description=f"Congratulations, your family **{role_name}** has been registered.",
                color=discord.Color.green(),
                timestamp=datetime.datetime.utcnow()
            )
            dm_embed.add_field(name="Family Creation Date", value=self.creation_date, inline=False)
            dm_embed.set_footer(text="Family Registration")
            await submitter.send(embed=dm_embed)
        except Exception:
            pass
        log_channel = guild.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            log_embed = discord.Embed(
                title="New Family Registered!",
                color=discord.Color.green(),
                timestamp=datetime.datetime.utcnow()
            )
            log_embed.add_field(name="Family", value=role_name, inline=False)
            log_embed.add_field(name="Leader", value=submitter.mention, inline=True)
            log_embed.add_field(name="Family Creation Date", value=self.creation_date, inline=True)
            log_embed.add_field(name="Family Logo", value=self.family_logo, inline=False)
            log_embed.add_field(name="Family Mansion", value=self.family_mansion, inline=False)
            log_embed.add_field(name="Approved by", value=interaction.user.mention, inline=False)
            await log_channel.send(embed=log_embed)
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.green()
        embed.title = f"✅ Approved - {embed.title}"
        await interaction.message.edit(embed=embed, view=None)
        await interaction.response.send_message("✅ Application approved.", ephemeral=True)
    @discord.ui.button(label="❌ Decline", style=discord.ButtonStyle.danger, custom_id="family_decline")
    async def decline_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Only administrators can decline applications.", ephemeral=True)
            return
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.red()
        embed.title = f"❌ Declined - {embed.title}"
        await interaction.message.edit(embed=embed, view=None)
        await interaction.response.send_message("❌ Application declined.", ephemeral=True)

class OpenModalView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="📝 Family Registration", style=discord.ButtonStyle.primary, custom_id="open_family_modal")
    async def open_modal(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(FamilyModal())

# ============================
#  FORM: Role Issuance Request (Text-based)
# ============================
class RoleRequestModal(discord.ui.Modal, title="Role Issuance Request"):
    discord_id = discord.ui.TextInput(
        label="Discord ID",
        placeholder="Enter the user's Discord ID (leave empty if unknown)",
        style=discord.TextStyle.short,
        max_length=30,
        required=False
    )
    player_nick = discord.ui.TextInput(
        label="Player Nickname",
        placeholder="Enter the player's nickname (if Discord ID is unknown)",
        style=discord.TextStyle.short,
        max_length=32,
        required=False
    )
    role_id = discord.ui.TextInput(
        label="Role ID",
        placeholder="Enter the Role ID",
        style=discord.TextStyle.short,
        max_length=30
    )
    reason = discord.ui.TextInput(
        label="Reason",
        placeholder="Specify the reason for issuing the role",
        style=discord.TextStyle.long,
        max_length=200
    )
    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        discord_id_str = self.discord_id.value.strip()
        if not discord_id_str:
            player_nick = self.player_nick.value.strip()
            if not player_nick:
                await interaction.response.send_message("❌ Please provide at least a Discord ID or Player Nickname.", ephemeral=True)
                return
            matches = [member for member in guild.members if member.display_name.lower() == player_nick.lower()]
            if not matches:
                await interaction.response.send_message(f"❌ User with nickname '{player_nick}' not found.", ephemeral=True)
                return
            discord_id_str = str(matches[0].id)
        embed = discord.Embed(
            title="📩 New Role Issuance Request",
            color=discord.Color.gold(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name="Discord ID", value=discord_id_str, inline=True)
        embed.add_field(name="Role ID", value=self.role_id.value, inline=True)
        embed.add_field(name="Reason", value=self.reason.value, inline=False)
        role_name_field = "Not found"
        discord_tag_field = "Not found"
        try:
            role_id_int = int(self.role_id.value.strip())
            role_obj = guild.get_role(role_id_int)
            if role_obj:
                role_name_field = role_obj.name
        except Exception:
            role_name_field = "Error"
        try:
            discord_id_int = int(discord_id_str)
            member_obj = guild.get_member(discord_id_int)
            if member_obj:
                discord_tag_field = member_obj.mention
        except Exception:
            discord_tag_field = "Error"
        embed.add_field(name="Role Name", value=role_name_field, inline=True)
        embed.add_field(name="User", value=discord_tag_field, inline=True)
        embed.set_footer(
            text=f"Request from {interaction.user}",
            icon_url=(interaction.user.avatar.url if interaction.user.avatar else None)
        )
        review_channel = guild.get_channel(ROLE_REQUEST_REVIEW_CHANNEL_ID)
        if review_channel is None:
            await interaction.response.send_message("❌ Error: review channel not found.", ephemeral=True)
            return
        view = RoleRequestReviewView(
            submitter_id=interaction.user.id,
            discord_id=discord_id_str,
            role_id=self.role_id.value,
            reason=self.reason.value
        )
        mention_text = f"<@&{ALERT_ROLE_ID}>"
        sent_message = await review_channel.send(content=mention_text, embed=embed, view=view)
        view.message = sent_message
        await interaction.response.send_message("✅ Your role issuance request has been sent for review.", ephemeral=True)

# ============================
#  FORM: Role Issuance Request (Selection-based)
# ============================
class UserSelect(discord.ui.Select):
    def __init__(self, guild: discord.Guild):
        options = []
        # Due to Discord's limitation of 25 options, taking the first 25 members
        for member in guild.members[:25]:
            options.append(discord.SelectOption(label=member.display_name, value=str(member.id)))
        super().__init__(placeholder="Select a user", min_values=1, max_values=1, options=options)
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.view.selected_user_id = int(self.values[0])

class RoleSelect(discord.ui.Select):
    def __init__(self, guild: discord.Guild):
        options = []
        base_role = guild.get_role(BASE_ASSIGNABLE_ROLE_ID)
        if base_role:
            filtered_roles = [r for r in guild.roles if r.name != "@everyone" and r.position < base_role.position]
        else:
            filtered_roles = [r for r in guild.roles if r.name != "@everyone"]
        filtered_roles.sort(key=lambda r: r.position, reverse=True)
        for role in filtered_roles[:25]:
            options.append(discord.SelectOption(label=role.name, value=str(role.id)))
        super().__init__(placeholder="Select a role", min_values=1, max_values=1, options=options)
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.view.selected_role_id = int(self.values[0])

class SubmitSelectButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Submit Request", style=discord.ButtonStyle.primary, custom_id="send_select_request")
    async def callback(self, interaction: discord.Interaction):
        view: RoleRequestSelectView = self.view
        if view.selected_user_id is None or view.selected_role_id is None:
            await interaction.response.send_message("Please select a user and a role.", ephemeral=True)
            return
        guild = view.guild
        member = guild.get_member(view.selected_user_id)
        role = guild.get_role(view.selected_role_id)
        discord_tag_field = member.mention if member else "Not found"
        role_name_field = role.name if role else "Not found"
        embed = discord.Embed(
            title="📩 New Role Issuance Request (Selection)",
            color=discord.Color.gold(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name="User", value=discord_tag_field, inline=True)
        embed.add_field(name="Role", value=role_name_field, inline=True)
        embed.add_field(name="Reason", value="Request via selection", inline=False)
        embed.set_footer(text=f"Request from {interaction.user}", icon_url=(interaction.user.avatar.url if interaction.user.avatar else None))
        if member and member.avatar:
            embed.set_thumbnail(url=member.avatar.url)
        if role and role.icon:
            embed.set_image(url=role.icon.url)
        review_channel = guild.get_channel(ROLE_REQUEST_REVIEW_CHANNEL_ID)
        if review_channel is None:
            await interaction.response.send_message("❌ Error: review channel not found.", ephemeral=True)
            return
        mention_text = f"<@&{ALERT_ROLE_ID}>"
        view2 = RoleRequestReviewView(
            submitter_id=interaction.user.id,
            discord_id=str(view.selected_user_id),
            role_id=str(view.selected_role_id),
            reason="Request via selection"
        )
        sent_message = await review_channel.send(content=mention_text, embed=embed, view=view2)
        view2.message = sent_message
        await interaction.response.send_message("✅ Your role issuance request has been sent for review.", ephemeral=True)

class RoleRequestSelectView(discord.ui.View):
    def __init__(self, guild: discord.Guild):
        super().__init__(timeout=None)
        self.guild = guild
        self.selected_user_id = None
        self.selected_role_id = None
        self.add_item(UserSelect(guild))
        self.add_item(RoleSelect(guild))
        self.add_item(SubmitSelectButton())

# ============================
#  FORM: Processing Role Issuance Request
# ============================
class RoleRequestReviewView(discord.ui.View):
    def __init__(self, submitter_id: int, discord_id: str, role_id: str, reason: str):
        super().__init__(timeout=None)
        self.submitter_id = submitter_id
        self.discord_id = discord_id
        self.role_id = role_id
        self.reason = reason
        self.message: discord.Message = None
    @discord.ui.button(label="✅ Approve", style=discord.ButtonStyle.success, custom_id="role_approve")
    async def approve_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Only administrators can approve requests.", ephemeral=True)
            return
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message("❌ Error: server not found.", ephemeral=True)
            return
        try:
            target_id = int(self.discord_id.strip())
        except ValueError:
            await interaction.response.send_message("❌ Error: invalid Discord ID.", ephemeral=True)
            return
        member = guild.get_member(target_id)
        if member is None:
            await interaction.response.send_message("❌ Error: user not found on the server.", ephemeral=True)
            return
        try:
            target_role_id = int(self.role_id.strip())
        except ValueError:
            await interaction.response.send_message("❌ Error: invalid Role ID.", ephemeral=True)
            return
        role = guild.get_role(target_role_id)
        if role is None:
            await interaction.response.send_message("❌ Error: role not found on the server.", ephemeral=True)
            return
        try:
            await member.add_roles(role, reason=self.reason)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error issuing role: {e}", ephemeral=True)
            return
        try:
            dm_embed = discord.Embed(
                title="You have been issued a new role!",
                description=f"Role **{role.name}** has been issued to you on server **{guild.name}**.",
                color=discord.Color.green(),
                timestamp=datetime.datetime.utcnow()
            )
            dm_embed.add_field(name="Reason", value=self.reason, inline=False)
            await member.send(embed=dm_embed)
        except Exception:
            pass
        log_channel = guild.get_channel(ROLE_REQUEST_LOG_CHANNEL_ID)
        if log_channel:
            log_embed = discord.Embed(
                title="Role Issuance Request Approved",
                color=discord.Color.green(),
                timestamp=datetime.datetime.utcnow()
            )
            log_embed.add_field(name="User", value=member.mention, inline=True)
            log_embed.add_field(name="Role", value=role.name, inline=True)
            log_embed.add_field(name="Reason", value=self.reason, inline=False)
            log_embed.add_field(name="Approved by", value=interaction.user.mention, inline=False)
            await log_channel.send(embed=log_embed)
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.green()
        embed.title = f"✅ Approved - {embed.title}"
        await interaction.message.edit(embed=embed, view=None)
        await interaction.response.send_message("✅ Role issuance request approved.", ephemeral=True)
    @discord.ui.button(label="❌ Decline", style=discord.ButtonStyle.danger, custom_id="role_decline")
    async def decline_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Only administrators can decline requests.", ephemeral=True)
            return
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.red()
        embed.title = f"❌ Declined - {embed.title}"
        await interaction.message.edit(embed=embed, view=None)
        await interaction.response.send_message("❌ Role issuance request declined.", ephemeral=True)

# ============================
#  Initial Presentation of Role Issuance System and Modals for Suggestions/Bug Reports
# ============================
class OpenRoleRequestModalView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="🛠 Role Request (ID)", style=discord.ButtonStyle.primary, custom_id="open_role_modal_text")
    async def open_modal_text(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not any(role.id == ALLOWED_REQUEST_ROLE_ID for role in interaction.user.roles if role.id != APPROVED):
            await interaction.response.send_message("❌ You do not have permission to use the role issuance system.", ephemeral=True)
            return
        await interaction.response.send_modal(RoleRequestModal())
    @discord.ui.button(label="🔽 Role Request (Selection)", style=discord.ButtonStyle.primary, custom_id="open_role_modal_select")
    async def open_modal_select(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not any(role.id == ALLOWED_REQUEST_ROLE_ID for role in interaction.user.roles):
            await interaction.response.send_message("❌ You do not have permission to use the role issuance system.", ephemeral=True)
            return
        view = RoleRequestSelectView(interaction.guild)
        await interaction.response.send_message("Select a user and role:", view=view, ephemeral=True)

class OpenSuggestionView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="💡 Suggest an Improvement", style=discord.ButtonStyle.primary, custom_id="open_suggestion_modal")
    async def open_suggestion(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SuggestionModal())

class OpenBugReportView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="🐞 Report a Bug", style=discord.ButtonStyle.danger, custom_id="open_bug_modal")
    async def open_bug(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(BugReportModal())

# ============================
#  MODAL WINDOWS: Suggestions and Bug Reports
# ============================
class SuggestionModal(discord.ui.Modal, title="Suggestion for Improving Empire RP Families"):
    suggestion = discord.ui.TextInput(
        label="Your Suggestion",
        placeholder="Describe what can be improved",
        style=discord.TextStyle.long,
        max_length=1000
    )
    async def on_submit(self, interaction: discord.Interaction):
        suggestion_channel = interaction.guild.get_channel(SUGGESTION_CHANNEL_ID)
        suggestion_channe = interaction.guild.get_channel(PREDOLOJ)
        if suggestion_channel is None:
            await interaction.response.send_message("❌ Suggestion channel not found.", ephemeral=True)
            return
        embed = discord.Embed(
            title="New Suggestion",
            description=self.suggestion.value,
            color=discord.Color.blurple(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_footer(text=f"From {interaction.user}", icon_url=(interaction.user.avatar.url if interaction.user.avatar else None))
        await suggestion_channe.send(embed=embed)
        await interaction.response.send_message("✅ Your suggestion has been sent.", ephemeral=True)

class BugReportModal(discord.ui.Modal, title="Report a Bug"):
    bug_description = discord.ui.TextInput(
        label="Bug Description",
        placeholder="Describe the issue, how to reproduce it, and any additional information",
        style=discord.TextStyle.long,
        max_length=1000
    )
    async def on_submit(self, interaction: discord.Interaction):
        bug_channel = interaction.guild.get_channel(BUG_REPORT_CHANNEL_ID)
        bug_channe = interaction.guild.get_channel(BUG)
        if bug_channel is None:
            await interaction.response.send_message("❌ Bug report channel not found.", ephemeral=True)
            return
        embed = discord.Embed(
            title="New Bug",
            description=self.bug_description.value,
            color=discord.Color.red(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_footer(text=f"From {interaction.user}", icon_url=(interaction.user.avatar.url if interaction.user.avatar else None))
        await bug_channe.send(embed=embed)
        await interaction.response.send_message("✅ Your bug report has been sent.", ephemeral=True)

# ============================
#            on_ready
# ============================
@bot.event
async def on_ready():
    print(f"Bot {bot.user} has successfully started!")
    # Message for family registration
    family_channel = bot.get_channel(INPUT_CHANNEL_ID)
    if family_channel:
        beauty_message = (
            "🌟 **Welcome to the Family Registration System!** 🌟\n\n"
            "To submit your family registration application, click the button below."
        )
        await family_channel.send(beauty_message, view=OpenModalView())
    # Message for the role issuance system
    role_request_channel = bot.get_channel(ROLE_REQUEST_INPUT_CHANNEL_ID)
    if role_request_channel:
        role_request_message = (
            "🔧 **Role Issuance System** 🔧\n\n"
            "If you need to receive a specific role, use one of the buttons below:\n"
            "• 🛠 Request via text form\n"
            "• 🔽 Request via user and role selection\n\n"
            f"To use the role issuance system, you must have the role with ID {ALLOWED_REQUEST_ROLE_ID}."
        )
        await role_request_channel.send(role_request_message, view=OpenRoleRequestModalView())
    # Message for suggestions
    suggestion_channel = bot.get_channel(SUGGESTION_CHANNEL_ID)
    if suggestion_channel:
        suggestion_message = (
            "💡 **Suggestions for Improving Empire RP Families**\n\n"
            "Click the button below to leave your suggestion."
        )
        await suggestion_channel.send(suggestion_message, view=OpenSuggestionView())
    # Message for bug reports
    bug_channel = bot.get_channel(BUG_REPORT_CHANNEL_ID)
    if bug_channel:
        bug_message = (
            "🐞 **Report a Bug with the Discord Bot**\n\n"
            "Click the button below to report an issue."
        )
        await bug_channel.send(bug_message, view=OpenBugReportView())

bot.run(TOKEN)
