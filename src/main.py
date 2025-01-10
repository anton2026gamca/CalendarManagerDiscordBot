import discord
from responses import *
from helpers import *
import os
from dotenv import load_dotenv
import datetime

settings = load_json("settings.json")

# Load token
load_dotenv()
TOKEN: str = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    print("TOKEN not loaded successfully")
    exit(1)

# Bot setup
intents: discord.Intents = discord.Intents.default()
intents.message_content = True
client: discord.Client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)

# Message functionality
async def send_message(message: discord.Message, user_message: str) -> None:
    if not user_message:
        return

    try:
        response: str = get_response(user_message)
        embed : discord.Embed = get_embed(user_message)
        if (response != "" or embed != None):
            await message.channel.send(response, embed=embed)
            print(f"[{message.channel}] {client.user.name}: {response}{embed}")
    except Exception as e:
        print("Error sending message:", e)

# Startup
@client.event
async def on_ready() -> None:
    print(f"{client.user} is now online")
    try:
        await tree.sync()
    except Exception as e:
        print(e)

# Handle incoming messages
@client.event
async def on_message(message: discord.Message) -> None:
    # Don't respond to it self
    if message.author == client.user:
        return

    username: str = str(message.author)
    user_message: str = message.content
    channel: str = str(message.channel)

    print(f"[{channel}] {username}: {user_message}")
    await send_message(message, user_message)

channels = load_json("channels.json")

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
        super().__init__()
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
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="list", description="List out all your events")
    async def event_list(self, interaction: discord.Interaction):
        server_id = interaction.guild_id
        user_id = interaction.user.id

        create_channel: bool = False
        channel = None
        channel_id: int = 0
        if channels.get(str(server_id)) is not None and channels[str(server_id)].get(str(user_id)) is not None:
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
            channel = await interaction.guild.create_text_channel(f"calendar-{interaction.user.name}", overwrites=overwrites, category=interaction.channel.category)
            channel_id = channel.id
            channels.setdefault(str(server_id), {})
            channels[str(server_id)][str(user_id)] = channel_id
            write_json("channels.json", channels)
        view = EventListView()
        await channel.send(embed=event_list_embed(server_id, user_id, interaction.user.roles), view=view)
        await interaction.response.send_message("Oh no ... you should not see this", ephemeral=True)
        await interaction.delete_original_response()
    
    @discord.app_commands.command(name="on_date", description="List out all commands on a specific date")
    @discord.app_commands.describe(month="Defaults to the current month", year="Defaults to the current year")
    async def event_on_date(self, interaction: discord.Interaction, day: int, month: int | None, year: int | None):
        if (month == None):
            month = datetime.date.today().month
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
        if calendars.get(str(server_id)) is not None:
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
            if settings.get(str(server_id)) is not None:
                has_permissions: bool = False
                user_roles_ids = []
                for role in interaction.user.roles:
                    user_roles_ids.append(role.id)
                if settings[str(server_id)].get("admin_role") is not None and user_roles_ids.__contains__(settings[str(server_id)]["admin_role"]):
                    has_permissions = True
                if settings[str(server_id)].get("trusted_role") is not None and user_roles_ids.__contains__(settings[str(server_id)]["trusted_role"]):
                    has_permissions = True
                if not has_permissions:
                    await interaction.response.send_message(embed=event_remove_nopermissions(), ephemeral=True)
                    return
        if calendars.get(str(server_id)) is not None:
            events = calendars[str(server_id)].get("events", [])
            for i in range(len(events)):
                event = events[i]
                if event["id"] == event_id:
                    await interaction.response.send_message(embed=event_remove_success(event), ephemeral=False)
                    calendars[str(server_id)].get("events", []).pop(i)
                    write_json("calendars.json", calendars)
                    return
        await interaction.response.send_message(embed=event_find_wrongid(event_id), ephemeral=True)

    @discord.app_commands.command(name="edit", description="Edit an event")
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
        discord.app_commands.Choice(name="Big Exam", value=3),
    ])
    async def event_edit(self, interaction: discord.Interaction, event_id: int, type: discord.app_commands.Choice[int] | None, name: str | None, description: str | None, subject: str | None, day: int | None, month: int | None, year: int | None):
        server_id = interaction.guild_id
        if interaction.user.id != interaction.guild.owner_id:
            if settings.get(str(server_id)) is not None:
                has_permissions: bool = False
                user_roles_ids = []
                for role in interaction.user.roles:
                    user_roles_ids.append(role.id)
                if settings[str(server_id)].get("admin_role") is not None and user_roles_ids.__contains__(settings[str(server_id)]["admin_role"]):
                    has_permissions = True
                if settings[str(server_id)].get("trusted_role") is not None and user_roles_ids.__contains__(settings[str(server_id)]["trusted_role"]):
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
        await interaction.response.send_message(embed=embed)

class SubjectGroup(discord.app_commands.Group):
    def __init__(self):
        super().__init__(name="subject", description="A school subject")

    @discord.app_commands.command(name="add", description="Add a subject, this can be only done if you are the server owner!")
    @discord.app_commands.describe(subject="The subject name to add", role="Role that a person has to have to add/see events of this subject")
    async def subject_add(self, interaction: discord.Interaction, subject: str, role: discord.Role):
        if (interaction.user.id != interaction.guild.owner_id):
            await interaction.response.send_message(embed=add_subject_nopermissions(), ephemeral=True)
            return
        server_id = interaction.guild_id
        subjects.setdefault(str(server_id), {"subjects": []})
        if subjects.get(str(server_id)) is not None:
            for obj in subjects[str(server_id)]["subjects"]:
                if obj["name"] == subject:
                    await interaction.response.send_message(embed=add_subject_exists(subject), ephemeral=True)
                    return
        subject_obj = {
            "name": subject,
            "role_id": role.id
        }
        subjects[str(server_id)]["subjects"].append(subject_obj)
        write_json("subjects.json", subjects)
        await interaction.response.send_message(embed=add_subject_success(subject, role), ephemeral=True)

    @discord.app_commands.command(name="list", description="Get all subjects that you can use/read")
    async def subjects_get(self, interaction: discord.Interaction):
        server_id: int = interaction.guild_id
        await interaction.response.send_message(embed=get_subjects_embed(server_id, interaction.user.roles, subjects), ephemeral=True)

def subject_exists(server_id: int, name: str) -> bool:
    if subjects.get(str(server_id)) is not None:
        for subj in subjects[str(server_id)]["subjects"]:
            if subj["name"] == name:
                return True
    return False

class SettingsSetGroup(discord.app_commands.Group):
    def __init__(self):
        super().__init__(name="set", description="Set bot settings")

    @discord.app_commands.command(name="admin_role", description="Set the admin role")
    @discord.app_commands.describe(role="Role to set the admin role to")
    async def settings_set_admin_role(self, interaction: discord.Interaction, role: discord.Role):
        if interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message(embed=settings_set_adminrole_nopermissions(), ephemeral=True)
            return
        server_id = interaction.guild_id
        if settings.get(str(server_id)) is None:
            settings[str(server_id)] = {}
        settings[str(server_id)]["admin_role"] = role.id
        write_json("settings.json", settings)
        await interaction.response.send_message(embed=settings_set_adminrole_success(role), ephemeral=True)

    @discord.app_commands.command(name="trusted_role", description="Set the \"trusted role\"")
    @discord.app_commands.describe(role="Role to set the trusted role to")
    async def settings_set_trusted_role(self, interaction: discord.Interaction, role: discord.Role):
        if interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message(embed=settings_set_trustedrole_nopermissions(), ephemeral=True)
            return
        server_id = interaction.guild_id
        if settings.get(str(server_id)) is None:
            settings[str(server_id)] = {}
        settings[str(server_id)]["trusted_role"] = role.id
        write_json("settings.json", settings)
        await interaction.response.send_message(embed=settings_set_trustedrole_success(role), ephemeral=True)

tree.add_command(EventGroup())
tree.add_command(SubjectGroup())
tree.add_command(SettingsSetGroup())

# Main entry point
def main() -> None:
    client.run(token=TOKEN)

if __name__ == "__main__":
    main()