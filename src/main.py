import discord
from responses import *
from helpers import *
import os
from dotenv import load_dotenv
import datetime
from bot_log import log

# Load token
load_dotenv()
TOKEN: str = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    log.critical("TOKEN didn't load successfully")
    exit(1)

# Bot setup
intents: discord.Intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
client: discord.Client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)

# Startup
settings = load_json("settings.json")
channels = load_json("channels.json")
            
@client.event
async def on_ready() -> None:
    log.info(f"Bot \"{client.user.name}\" is now running!")
    try:
        await tree.sync()
    except Exception as e:
        log.error(e)

# Handle incoming messages
@client.event
async def on_message(message: discord.Message) -> None:
    # Don't respond to it self
    if message.author == client.user:
        return

    log.debug(f"[{message.guild.name} > {message.channel.name}] {message.author.name}: {message.content}")
    
    if message.content == "!resolved" and isinstance(message.channel, discord.Thread) and str(message.guild.id) in settings and "admin_role" in settings[str(message.guild.id)]:
        for role in message.author.roles:
            if role.id == settings[str(message.guild.id)]["admin_role"]:
                await message.channel.send(embed=problem_resolved(message.author.mention))
                thread_starter_message = await message.channel.parent.fetch_message(message.channel.id)
                if thread_starter_message:
                    for reaction in thread_starter_message.reactions:
                        await reaction.remove(client.user)
                    await thread_starter_message.add_reaction('✅')
                await message.delete()
                break
    
    if str(message.guild.id) in settings:
        if (message.channel.id == settings[str(message.guild.id)]["help_channel"]):
            thread_name: str = message.content
            if "<@&" in thread_name:
                mention_start = thread_name.find("<@&")
                mention_end = mention_start + thread_name[mention_start:].find(">") + 1
                thread_name = thread_name[:mention_start] + thread_name[mention_end:]
            thread = await message.create_thread(name=thread_name)
            await message.add_reaction('🤔')
            if "admin_role" in settings[str(message.guild.id)]:
                admin_role: str = settings[str(message.guild.id)]["admin_role"]
                if f"<@&{admin_role}>" in message.content:
                    await thread.send(f"Hmmmmm... I don't know, you will have to wait for the admins!")
                else:
                    await thread.send(f"Hmmmmm... I don't know, you will have to wait for the admins! I'll call em ... <@&{admin_role}>")
            else:
                await thread.send(f"Hmmmmm... I don't know, you will have to wait for the admins!")

def subject_by_name(server_id: int, name: str) -> int:
    if str(server_id) in subjects:
        for i in range(len(subjects[str(server_id)]["subjects"])):
            if subjects[str(server_id)]["subjects"][i]["name"] == name:
                return i
    return -1

def subject_exists(server_id: int, name: str) -> bool:
    if str(server_id) in subjects:
        for subj in subjects[str(server_id)]["subjects"]:
            if subj["name"] == name:
                return True
    return False

class UpdateEventListButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Refresh", style=discord.ButtonStyle.primary, custom_id="update_message_button")

    async def callback(self, interaction: discord.Interaction):
        server_id = interaction.guild_id
        user_id = interaction.user.id
        view = EventListView()
        await interaction.response.edit_message(embed=event_list_embed(server_id, user_id, interaction.user.roles), view=view)

class EventListView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(UpdateEventListButton())

class EventGroup(discord.app_commands.Group):
    def __init__(self):
        super().__init__(name="event", description="An event")

    @discord.app_commands.command(name="add", description="Add an event")
    @discord.app_commands.describe(type="Type of the event",
                                   name="Name of the event",
                                   description="The description of the event",
                                   subject="\"Predmet\"",
                                   day="Day of the event",
                                   month="Month of the event",
                                   year="(optional, default is the current year) Year of the event")
    @discord.app_commands.choices(type=[
        discord.app_commands.Choice(name="Homework", value=1),
        discord.app_commands.Choice(name="Exam", value=2),
        discord.app_commands.Choice(name="Big Exam", value=3),
    ])
    async def event_add(self, interaction: discord.Interaction, type: discord.app_commands.Choice[int], name: str, description: str | None, subject: str, day: int, month: int, year: int | None):
        server_id = interaction.guild_id
        if description is None:
            description = ""
        if (year == None):
            year = datetime.date.today().year
        if not is_date_valid(day, month, year):
            await interaction.response.send_message(embed=ivalid_date(day, month, year), ephemeral=True)
            return
        if not subject_exists(server_id, subject):
            await interaction.response.send_message(embed=event_add_subjectnotvalid(server_id, interaction.user.roles, subject, subjects), ephemeral=True)
            return
        embed: discord.Embed = calendar_event_add(interaction.guild_id, type.name, name, description, subject, day, month, year)
        subject_i = subject_by_name(server_id, subject)
        if subjects[str(server_id)]["subjects"][subject_i].get("channel") is not None and subjects[str(server_id)]["subjects"][subject_i]["channel"] > -1:
            await interaction.guild.get_channel(subjects[str(server_id)]["subjects"][subject_i]["channel"]).send(embed=embed)
            await interaction.response.send_message("Oh no ... you should not see this", ephemeral=True)
            await interaction.delete_original_response()
        else:
            await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="list", description="List out all your events")
    async def event_list(self, interaction: discord.Interaction):
        server_id = interaction.guild_id
        user_id = interaction.user.id

        create_channel: bool = False
        channel = None
        channel_id: int = 0
        if str(server_id) in channels and str(user_id) in channels[str(server_id)]:
            channel_id: int = channels[str(server_id)][str(user_id)]
            channel = interaction.guild.get_channel(channel_id)
            if channel is None:
                create_channel = True
        else:
            create_channel = True
        if create_channel:
            overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
                interaction.user: discord.PermissionOverwrite(view_channel=True),
            }
            category_id = -1
            if str(server_id) in settings and "calendar_category" in settings[str(server_id)]:
                category_id = settings[str(server_id)]["calendar_category"]
            category: discord.CategoryChannel = None
            if category_id > -1:
                category: discord.CategoryChannel = interaction.guild.get_channel(category_id)
            channel: discord.TextChannel
            if category is not None:
                channel = await interaction.guild.create_text_channel(f"calendar-{interaction.user.name}", overwrites=overwrites, category=category)
            else:
                channel = await interaction.guild.create_text_channel(f"calendar-{interaction.user.name}", overwrites=overwrites)
            channel_id = channel.id
            channels.setdefault(str(server_id), {})
            channels[str(server_id)][str(user_id)] = channel_id
            write_json("channels.json", channels)
        view = EventListView()
        await channel.send(embed=event_list_embed(server_id, user_id, interaction.user.roles), view=view)
        await interaction.response.send_message("Oh no ... you should not see this", ephemeral=True)
        await interaction.delete_original_response()
    
    @discord.app_commands.command(name="on_date", description="List out all your event on a specific date")
    @discord.app_commands.describe(month="Defaults to the current month", year="Defaults to the current year")
    async def event_on_date(self, interaction: discord.Interaction, day: int, month: int, year: int | None):
        if (year == None):
            year = datetime.date.today().year
        if (is_date_valid(day, month, year)):
            await interaction.response.send_message(embed=event_on_date(interaction.guild_id, interaction.user.roles, day, month, year), ephemeral=True)
        else:
            await interaction.response.send_message(embed=ivalid_date(day, month, year), ephemeral=True)

    @discord.app_commands.command(name="info", description="Get more info about an event")
    @discord.app_commands.describe(event_id="The ID of the event to get info of")
    async def event_info(self, interaction: discord.Interaction, event_id: int):
        server_id = interaction.guild_id
        if str(server_id) in calendars:
            for event in calendars[str(server_id)].get("events", []):
                if event["id"] == event_id:
                    await interaction.response.send_message(embed=event_info_embed(event), ephemeral=True)
                    return
        await interaction.response.send_message(embed=event_find_wrongid(event_id), ephemeral=True)

    @discord.app_commands.command(name="remove", description="Remove an event")
    @discord.app_commands.describe(event_id="The ID of the event to remove")
    async def event_remove(self, interaction: discord.Interaction, event_id: int):
        server_id = interaction.guild_id
        if interaction.user.id != interaction.guild.owner_id:
            if str(server_id) in settings:
                has_permissions: bool = False
                user_roles_ids = []
                for role in interaction.user.roles:
                    user_roles_ids.append(role.id)
                if "admin_role" in settings[str(server_id)] and user_roles_ids.__contains__(settings[str(server_id)]["admin_role"]):
                    has_permissions = True
                if "trusted_role" in settings[str(server_id)] and user_roles_ids.__contains__(settings[str(server_id)]["trusted_role"]):
                    has_permissions = True
                if not has_permissions:
                    await interaction.response.send_message(embed=event_remove_nopermissions(), ephemeral=True)
                    return
        if str(server_id) in calendars:
            events = calendars[str(server_id)].get("events", [])
            for i in range(len(events)):
                event = events[i]
                if event["id"] == event_id:
                    embed: discord.Embed = event_remove_success(event)
                    subject_i = subject_by_name(server_id, event["subject"])
                    if subjects[str(server_id)]["subjects"][subject_i]["channel"] > -1:
                        await interaction.guild.get_channel(subjects[str(server_id)]["subjects"][subject_i]["channel"]).send(embed=embed)
                        await interaction.response.send_message("Oh no ... you should not see this", ephemeral=True)
                        await interaction.delete_original_response()
                    else:
                        await interaction.response.send_message(embed=embed, ephemeral=False)
                    calendars[str(server_id)].get("events", []).pop(i)
                    write_json("calendars.json", calendars)
                    return
        await interaction.response.send_message(embed=event_find_wrongid(event_id), ephemeral=True)

    @discord.app_commands.command(name="edit", description="Edit an event.")
    @discord.app_commands.describe(event_id="The ID of the event to edit",
                                   type="Type of the event",
                                   name="Name of the event",
                                   description="The description of the event",
                                   subject="\"Predmet\"",
                                   day="Day of the event",
                                   month="Month of the event",
                                   year="(optional, default is the current year) Year of the event")
    @discord.app_commands.choices(type=[
        discord.app_commands.Choice(name="Homework", value=1),
        discord.app_commands.Choice(name="Exam", value=2),
        discord.app_commands.Choice(name="Other", value=3),
    ])
    async def event_edit(self, interaction: discord.Interaction, event_id: int, type: discord.app_commands.Choice[int] | None, name: str | None, description: str | None, subject: str | None, day: int | None, month: int | None, year: int | None):
        server_id = interaction.guild_id
        if interaction.user.id != interaction.guild.owner_id:
            if str(server_id) in settings:
                has_permissions: bool = False
                user_roles_ids = []
                for role in interaction.user.roles:
                    user_roles_ids.append(role.id)
                if "admin_role" in settings[str(server_id)] and user_roles_ids.__contains__(settings[str(server_id)]["admin_role"]):
                    has_permissions = True
                if "trusted_role" in settings[str(server_id)] is not None and user_roles_ids.__contains__(settings[str(server_id)]["trusted_role"]):
                    has_permissions = True
                if not has_permissions:
                    await interaction.response.send_message(embed=event_edit_nopermissions(), ephemeral=True)
                    return
        if subject is not None and not subject_exists(server_id, subject):
            await interaction.response.send_message(embed=event_edit_subjectnotvalid(server_id, interaction.user.roles, subject, subjects), ephemeral=True)
            return
        type_name: str | None = None
        if type is not None:
            type_name = type.name
        event_index: int = -1
        calendars.setdefault(str(server_id), {"events": []})
        if str(server_id) in calendars:
            for i in range(len(calendars[str(server_id)].get("events", []))):
                event = calendars[str(server_id)]["events"][i]
                if event["id"] == event_id:
                    event_index = i
                    break
        if event_index == -1:
            await interaction.response.send_message(embed=event_find_wrongid(event_id), ephemeral=True)
            return
        embed: discord.Embed = calendar_event_edit(interaction.guild_id, event_index, type_name, name, description, subject, day, month, year)
        subject_i = subject_by_name(server_id, subject)
        if subjects[str(server_id)]["subjects"][subject_i]["channel"] > -1:
            await interaction.guild.get_channel(subjects[str(server_id)]["subjects"][subject_i]["channel"]).send(embed=embed)
            await interaction.response.send_message("Oh no ... you should not see this", ephemeral=True)
            await interaction.delete_original_response()
        else:
            await interaction.response.send_message(embed=embed)

class SubjectGroup(discord.app_commands.Group):
    def __init__(self):
        super().__init__(name="subject", description="A school subject")

    @discord.app_commands.command(name="add", description="Add a subject. (If you are the server owner)")
    @discord.app_commands.describe(subject="The subject name to add", role="Role that a person has to have to add/see events of this subject", updates_channel="A channel where the bot will post updates about the subject (add event, edit event, ...)")
    async def subject_add(self, interaction: discord.Interaction, subject: str, role: discord.Role, updates_channel: discord.TextChannel | None):
        if (interaction.user.id != interaction.guild.owner_id):
            await interaction.response.send_message(embed=add_subject_nopermissions(), ephemeral=True)
            return
        server_id = interaction.guild_id
        if (subject_exists(server_id, subject)):
            await interaction.response.send_message(embed=add_subject_exists(subject), ephemeral=True)
            return
        subject_obj = {
            "name": subject,
            "role_id": role.id,
            "channel": updates_channel.id if updates_channel is not None else -1
        }
        if str(server_id) not in subjects:
            subjects[str(server_id)] = {}
        if "subjects" not in subjects[str(server_id)]:
            subjects[str(server_id)]["subjects"] = []
        subjects[str(server_id)]["subjects"].append(subject_obj)
        subjects[str(server_id)]["subjects"] = sorted(subjects[str(server_id)]["subjects"], key=lambda x: x["name"])
        write_json("subjects.json", subjects)
        await interaction.response.send_message(embed=add_subject_success(subject, role, updates_channel), ephemeral=True)
        
    @discord.app_commands.command(name="edit", description="Edit a subjects name/role. (If you are the server owner)")
    @discord.app_commands.describe(old_name="Subject to edit name", new_name="New name of the subject", new_role="New role of the subject", new_channel="New channel to post updates of the subject")
    async def subject_edit(self, interaction: discord.Interaction, old_name: str, new_name: str | None, new_role: discord.Role | None, new_channel : discord.TextChannel | None):
        if (interaction.user.id != interaction.guild.owner_id):
            await interaction.response.send_message(embed=edit_subject_nopermissions(), ephemeral=True)
            return
        server_id: int = interaction.guild_id
        i: int = subject_by_name(server_id, old_name)
        if i < 0:
            await interaction.response.send_message(embed=edit_subject_doesnotexist(old_name), ephemeral=True)
            return
        old_role_id = subjects[str(server_id)]["subjects"][i]["role_id"]
        new_role_id = old_role_id
        old_channel_id = -1
        new_channel_id = -1
        if "channel" in subjects[str(server_id)]["subjects"][i]:
            old_channel_id = subjects[str(server_id)]["subjects"][i]["channel"]
            new_channel_id = old_channel_id
        if new_name is not None:
            subjects[str(server_id)]["subjects"][i]["name"] = new_name
        if new_role is not None:
            subjects[str(server_id)]["subjects"][i]["role_id"] = new_role.id
            new_role_id = new_role.id
        if new_channel is not None:
            subjects[str(server_id)]["subjects"][i]["channel"] = new_channel.id
            new_channel_id = new_channel.id
        subjects[str(server_id)]["subjects"] = sorted(subjects[str(server_id)]["subjects"], key=lambda x: x["name"])
        write_json("subjects.json", subjects)
        await interaction.response.send_message(embed=edit_subject_success(old_name, new_name if new_name is not None else old_name, old_role_id, new_role_id, old_channel_id, new_channel_id), ephemeral=True)
        
    @discord.app_commands.command(name="remove", description="Remove a subject. (If you are the server owner)")
    @discord.app_commands.describe(name="Subject name to delte")
    async def subject_remove(self, interaction: discord.Interaction, name: str):
        if (interaction.user.id != interaction.guild.owner_id):
            await interaction.response.send_message(embed=remove_subject_nopermissions(), ephemeral=True)
            return
        server_id: int = interaction.guild_id
        i: int = subject_by_name(server_id, name)
        if i < 0:
            await interaction.response.send_message(embed=remove_subject_doesnotexist(name), ephemeral=True)
            return
        subjects[str(server_id)]["subjects"].pop(i)
        write_json("subjects.json", subjects)
        await interaction.response.send_message(embed=remove_subject_success(name), ephemeral=True)
        
    @discord.app_commands.command(name="list", description="List out all subjects that you can use")
    async def subject_list(self, interaction: discord.Interaction):
        server_id: int = interaction.guild_id
        await interaction.response.send_message(embed=get_subjects_embed(server_id, interaction.user.roles, subjects), ephemeral=True)
        
class SetGroup(discord.app_commands.Group):
    def __init__(self):
        super().__init__(name="set", description="Set bot settings", default_permissions=discord.Permissions(1, administrator=True))

    @discord.app_commands.command(name="admin_role", description="People with this role can edit/remove events and mark questions in the help channel as resolved")
    @discord.app_commands.describe(role="Role to set the admin role to")
    async def set_admin_role(self, interaction: discord.Interaction, role: discord.Role):
        if interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message(embed=set_adminrole_nopermissions(), ephemeral=True)
            return
        server_id = interaction.guild_id
        if str(server_id) not in  settings:
            settings[str(server_id)] = {}
        settings[str(server_id)]["admin_role"] = role.id
        write_json("settings.json", settings)
        await interaction.response.send_message(embed=set_adminrole_success(role), ephemeral=True)

    @discord.app_commands.command(name="trusted_role", description="People with this role can edit/remove events")
    @discord.app_commands.describe(role="Role to set the trusted role to")
    async def set_trusted_role(self, interaction: discord.Interaction, role: discord.Role):
        if interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message(embed=set_trustedrole_nopermissions(), ephemeral=True)
            return
        server_id = interaction.guild_id
        if str(server_id) not in  settings:
            settings[str(server_id)] = {}
        settings[str(server_id)]["trusted_role"] = role.id
        write_json("settings.json", settings)
        await interaction.response.send_message(embed=set_trustedrole_success(role), ephemeral=True)
        
    @discord.app_commands.command(name="help_channel", description="Set the help channel. I'll help you manage it!")
    async def set_help_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message(embed=set_helpchannel_nopermissions(), ephemeral=True)
            return
        server_id = interaction.guild_id
        if str(server_id) not in  settings:
            settings[str(server_id)] = {}
        settings[str(server_id)]["help_channel"] = channel.id
        write_json("settings.json", settings)
        await interaction.response.send_message(embed=set_helpchannel_success(channel), ephemeral=True)
    
    @discord.app_commands.command(name="calendar_category", description="Set the category where the calendar channels for people will be created")
    async def set_calendar_category(self, interaction: discord.Interaction, category: discord.CategoryChannel):
        if interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message(embed=set_calendarcategory_nopermissions(), ephemeral=True)
            return
        server_id = interaction.guild_id
        if str(server_id) not in  settings:
            settings[str(server_id)] = {}
        settings[str(server_id)]["calendar_category"] = category.id
        write_json("settings.json", settings)
        await interaction.response.send_message(embed=set_calendarcategory_success(category), ephemeral=True)
    
class GetGroup(discord.app_commands.Group):
    def __init__(self):
        super().__init__(name="get", description="Set bot settings", default_permissions=discord.Permissions(1, administrator=True))

    @discord.app_commands.command(name="admin_role")
    async def get_admin_role(self, interaction: discord.Interaction):
        server_id = interaction.guild_id
        if str(server_id) not in  settings:
            settings[str(server_id)] = {}
        if "admin_role" in settings[str(server_id)]:
            role_id = settings[str(server_id)]["admin_role"]
            await interaction.response.send_message(embed=get_adminrole(role_id), ephemeral=True)
        else:
            await interaction.response.send_message(embed=get_adminrole(None), ephemeral=True)
        
    @discord.app_commands.command(name="trusted_role")
    async def get_trusted_role(self, interaction: discord.Interaction):
        server_id = interaction.guild_id
        if str(server_id) not in  settings:
            settings[str(server_id)] = {}
        if "trusted_role" in settings[str(server_id)]:
            role_id = settings[str(server_id)]["trusted_role"]
            await interaction.response.send_message(embed=get_trustedrole(role_id), ephemeral=True)
        else:
            await interaction.response.send_message(embed=get_trustedrole(None), ephemeral=True)
            
    @discord.app_commands.command(name="help_channel")
    async def get_trusted_role(self, interaction: discord.Interaction):
        server_id = interaction.guild_id
        if str(server_id) not in  settings:
            settings[str(server_id)] = {}
        if "help_channel" in settings[str(server_id)]:
            channel_id = settings[str(server_id)]["help_channel"]
            await interaction.response.send_message(embed=get_helpchannel(channel_id), ephemeral=True)
        else:
            await interaction.response.send_message(embed=get_helpchannel(None), ephemeral=True)
            
    @discord.app_commands.command(name="calendar_category")
    async def get_calendar_category(self, interaction: discord.Interaction):
        server_id = interaction.guild_id
        if str(server_id) not in  settings:
            settings[str(server_id)] = {}
        if "calendar_category" in settings[str(server_id)]:
            channel_id = settings[str(server_id)]["calendar_category"]
            await interaction.response.send_message(embed=get_calendarcategory(channel_id), ephemeral=True)
        else:
            await interaction.response.send_message(embed=get_calendarcategory(None), ephemeral=True)
            
    @discord.app_commands.command(name="all_subjects")
    async def get_all_subjects(self, interaction: discord.Interaction):
        server_id = interaction.guild_id
        await interaction.response.send_message(embed=get_all_subjects_embed(server_id, interaction.user.roles, subjects), ephemeral=True)
        
    @discord.app_commands.command(name="subject_info")
    async def get_subject_info(self, interaction: discord.Interaction, id: int):
        server_id = interaction.guild_id
        if not str(server_id) in subjects:
            await interaction.response.send_message(embed=get_subject_info_not_found(id), ephemeral=True)
            return
        if not "subjects" in subjects[str(server_id)]:
            await interaction.response.send_message(embed=get_subject_info_not_found(id), ephemeral=True)
            return
        if len(subjects[str(server_id)]["subjects"]) <= id:
            await interaction.response.send_message(embed=get_subject_info_not_found(id), ephemeral=True)
            return
        subject = subjects[str(server_id)]["subjects"][id]
        await interaction.response.send_message(embed=get_subject_info(subject), ephemeral=True)

@tree.command(name="help", description="I'll help you out")
async def help(interaction: discord.Interaction):
    server_id = interaction.guild_id
    admin_role_id = -1
    trusted_role_id = -1
    help_channel_id = -1
    if str(server_id) in settings:
        if "admin_role" in settings[str(server_id)] is not None:
            admin_role_id = settings[str(server_id)]["admin_role"]
        if "trusted_role" in settings[str(server_id)] is not None:
            trusted_role_id = settings[str(server_id)]["trusted_role"]
        if settings[str(server_id)].get("help_channel") is not None:
            help_channel_id = settings[str(server_id)]["help_channel"]
    admin_role: str = f"<@&{admin_role_id}>" if admin_role_id > -1 else "admin"
    trusted_role: str = f"<@&{trusted_role_id}>" if trusted_role_id > -1 else "trusted"

    embed = discord.Embed(
        title="Help",
        color=discord.Color.blue()
    )
    embed.add_field(name="", value=f"", inline=False)
    embed.add_field(name="Commands", value=f"", inline=False)
        
    commands = tree.get_commands()
    filtered_commands = [cmd for cmd in commands if cmd.name != "help"]
    for cmd in filtered_commands:
        if isinstance(cmd, discord.app_commands.Group):
            if cmd.name == "set" or cmd.name == "get":
                continue
            for sub_cmd in cmd.commands:
                if cmd.name == "subject" and sub_cmd.name != "list":
                    continue
                description: str = sub_cmd.description
                if cmd.name == "event" and (sub_cmd.name == "edit" or sub_cmd.name == "remove"):
                    description += f" This can be done only by people with the {trusted_role} or {admin_role} role!"
                if sub_cmd.name == "help_channel":
                    description += f" If you write a message in the help channel, the bot will create a public thread and react with a 🤔. Then, a person with the {admin_role} role can type `!resolved` and the bot will react with ✅"
                embed.add_field(name="", value=f"`/{cmd.name} {sub_cmd.name}` - {description}\n", inline=False)
        else:
            embed.add_field(name="", value=f"`/{cmd.name}` - {cmd.description}\n", inline=False)
    if help_channel_id > -1:
        embed.add_field(name="", value=f"", inline=False)
        embed.add_field(name="Need help?", value=f"Just ask a question in the <#{help_channel_id}> channel", inline=False)
        
    await interaction.response.send_message(embed=embed)

tree.add_command(EventGroup())
tree.add_command(SubjectGroup())
tree.add_command(SetGroup())
tree.add_command(GetGroup())

# Main entry point
def main() -> None:
    client.run(token=TOKEN)

if __name__ == "__main__":
    main()