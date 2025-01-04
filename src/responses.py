import discord
from random import randint
from helpers import *

calendars = load_json("calendars.json")
subjects = load_json("subjects.json")

def event_list_embed(server_id: int, user_id: int, user_roles: discord.Role) -> discord.Embed:
    embed = discord.Embed(
        title="Your events",
        color=discord.Color.blue()
    )
    num_events: int = 0
    if calendars.get(str(server_id)) is not None:
        for event in calendars[str(server_id)].get("events", []):
            type: str = event["type"]
            name: str = event["name"]
            subject: str = event["subject"]
            day: int = event["day"]
            month: int = event["month"]
            year: int = event["year"]
            date: str = f"{day}.{month}. {year}"
            id: int = event["id"]
            visible = False
            if subjects.get(f"{server_id}", []) is not None:
                for s in subjects[f"{server_id}"]["subjects"]:
                    if s["name"] == subject:
                        for role in user_roles:
                            if role.id == s["role_id"]:
                                visible = True
            else:
                subject[f"{server_id}"] = {"subjects": []}
            if (visible):
                embed.add_field(name="", value=f":white_small_square: **{subject}** - **{type}** - {name}\nㅤㅤ`{date}`ㅤ(id: `{id}`)`", inline=False)
                num_events += 1
    if (num_events == 0):
        embed.add_field(name="", value="You dont have any events", inline=False)
    else:
        embed.add_field(name="", value="Use `/event info [event id]` for more info", inline=False)
    return embed

def event_add_error(error_message: str) -> discord.Embed:
    embed = discord.Embed(
        title="Failed to create event",
        color=discord.Color.red()
    )
    embed.add_field(name="", value=error_message, inline=False)
    return embed

def event_add_subjectnotvalid(server_id: int, user_roles: discord.Role, subject: str, subjects) -> discord.Embed:
    embed = discord.Embed(
        title="Failed to create event",
        color=discord.Color.red()
    )
    embed.add_field(name="", value=f"Subject \"{subject}\" does not exist", inline=False)
    text: str = get_subjects_text(server_id, user_roles, subjects)
    embed.add_field(name="", value=text, inline=False)
    return embed

def calendar_event_add(server_id: int, type: str, name: str, description: str, subject: str, day: int, month: int, year: int) -> discord.Embed:
    next_event_id: int = 0
    if str(server_id) in calendars:
        if "next_event_id" in calendars[str(server_id)]:
            next_event_id = calendars[str(server_id)]["next_event_id"]

    calendars.setdefault(str(server_id), {"events": []})
    event = {
        "type": type,
        "name": name,
        "description": description,
        "subject": subject,
        "day": day,
        "month": month,
        "year": year,
        "id": next_event_id
    }
    calendars[str(server_id)]["next_event_id"] = next_event_id + 1
    calendars[str(server_id)]["events"].append(event)
    write_json("calendars.json", calendars)

    embed = discord.Embed(
        title="Created Event Successfully",
        color=discord.Color.green()
    )
    embed.add_field(name="Type", value=type, inline=True)
    embed.add_field(name="Subject", value=subject, inline=True)
    embed.add_field(name="Date", value=f"{day}.{month}. {year}", inline=True)
    embed.add_field(name="ID", value=next_event_id, inline=True)
    embed.add_field(name="Name", value=name, inline=True)
    embed.add_field(name="Description", value=description, inline=True)
    return embed

def event_find_wrongid(id: int) -> discord.Embed:
    embed = discord.Embed(
        title="Failed to find event",
        color=discord.Color.red()
    )
    embed.add_field(name="", value=f"Failed to find evend with id `{id}`", inline=False)
    return embed

def event_info_embed(event) -> discord.Embed:
    type: str = event["type"]
    name: str = event["name"]
    description: str = event["description"]
    subject: str = event["subject"]
    day: int = event["day"]
    month: int = event["month"]
    year: int = event["year"]
    date: str = f"{day}.{month}. {year}"
    id: int = event["id"]

    text = f"Date: `{date}`\nId: `{id}`"
    if description != "":
        text += f"\nDescription: {description}"
    
    embed = discord.Embed(
        title=f"{subject} - {type}",
        color=discord.Color.blue()
    )
    embed.add_field(name=name, value=text, inline=False)
    return embed

def event_remove_nopermissions():
    embed = discord.Embed(
        title=f"Failed to remove event",
        color=discord.Color.red()
    )
    embed.add_field(name="", value="You don't have permissions to do this", inline=False)
    return embed

def event_edit_nopermissions():
    embed = discord.Embed(
        title=f"Failed to edit event",
        color=discord.Color.red()
    )
    embed.add_field(name="", value="You don't have permissions to do this", inline=False)
    return embed

def event_edit_subjectnotvalid(server_id: int, user_roles: discord.Role, subject: str, subjects) -> discord.Embed:
    embed = discord.Embed(
        title="Failed to edit event",
        color=discord.Color.red()
    )
    embed.add_field(name="", value=f"Subject \"{subject}\" does not exist", inline=False)
    text: str = get_subjects_text(server_id, user_roles, subjects)
    embed.add_field(name="", value=text, inline=False)
    return embed

def calendar_event_edit(server_id: int, event_index: int, type: str | None, name: str | None, description: str | None, subject: str | None, day: int | None, month: int | None, year: int | None) -> discord.Embed:
    if type is None:
        type = calendars[str(server_id)]["events"][event_index]["type"]
    if name is None:
        name = calendars[str(server_id)]["events"][event_index]["name"]
    if description is None:
        description = calendars[str(server_id)]["events"][event_index]["description"]
    if subject is None:
        subject = calendars[str(server_id)]["events"][event_index]["subject"]
    if day is None:
        day = calendars[str(server_id)]["events"][event_index]["day"]
    if month is None:
        month = calendars[str(server_id)]["events"][event_index]["month"]
    if year is None:
        year = calendars[str(server_id)]["events"][event_index]["year"]
    id = calendars[str(server_id)]["events"][event_index]["id"]
    calendars[str(server_id)]["events"][event_index]["type"] = type
    calendars[str(server_id)]["events"][event_index]["name"] = name
    calendars[str(server_id)]["events"][event_index]["description"] = description
    calendars[str(server_id)]["events"][event_index]["subject"] = subject
    calendars[str(server_id)]["events"][event_index]["day"] = day
    calendars[str(server_id)]["events"][event_index]["month"] = month
    calendars[str(server_id)]["events"][event_index]["year"] = year
    write_json("calendars.json", calendars)

    embed = discord.Embed(
        title="Edited Event Successfully",
        color=discord.Color.green()
    )
    embed.add_field(name="Type", value=type, inline=True)
    embed.add_field(name="Subject", value=subject, inline=True)
    embed.add_field(name="Date", value=f"{day}.{month}. {year}", inline=True)
    embed.add_field(name="ID", value=id, inline=True)
    embed.add_field(name="Name", value=name, inline=True)
    embed.add_field(name="Description", value=description, inline=True)
    return embed

def event_remove_success(event):
    type: str = event["type"]
    name: str = event["name"]
    description: str = event["description"]
    subject: str = event["subject"]
    day: int = event["day"]
    month: int = event["month"]
    year: int = event["year"]
    date: str = f"{day}.{month}. {year}"
    id: int = event["id"]

    text = f"{subject} - {type}\nName: {name}\nDate: `{date}`\nId: `{id}`"
    if description != "":
        text += f"\nDescription: {description}"
    
    embed = discord.Embed(
        title=f"Event removed",
        color=discord.Color.red()
    )
    embed.add_field(name="", value=text, inline=False)
    return embed

def add_subject_exists(subject: str) -> discord.Embed:
    embed = discord.Embed(
        title="Failed to add subject",
        color=discord.Color.red()
    )
    embed.add_field(name="", value=f"Subject \"{subject}\" already exists!", inline=True)
    return embed

def add_subject_nopermissions() -> discord.Embed:
    embed = discord.Embed(
        title="Failed to add subject",
        color=discord.Color.red()
    )
    embed.add_field(name="", value=f"You MUST be the server owner to do this!", inline=True)
    return embed

def add_subject_success(subject: str, role: discord.Role) -> discord.Embed:
    embed = discord.Embed(
        title="Added Subject Successfully",
        color=discord.Color.green()
    )
    embed.add_field(name="", value=f"Subject: {subject}\nRole: {role.mention}", inline=True)
    return embed

def get_subjects_embed(server_id: int, user_roles: discord.Role, subjects) -> discord.Embed:
    embed = discord.Embed(
        title="",
        color=discord.Color.red()
    )
    text = get_subjects_text(server_id, user_roles, subjects)
    embed.add_field(name="", value=text, inline=False)
    return embed

def get_subjects_text(server_id: int, user_roles: discord.Role, subjects) -> str:
    text: str = "Subjects you can use:\n"
    num_subjects: int = 0
    if subjects.get(str(server_id)) is not None:
        user_roles_id = []
        for role in user_roles:
            user_roles_id.append(role.id)
        for subj in subjects[str(server_id)]["subjects"]:
            if user_roles_id.__contains__(subj["role_id"]):
                name: str = subj["name"]
                text += f":white_small_square:{name}\n"
                num_subjects += 1
    if (num_subjects == 0):
        text = "There are no subjects"
    return text

def settings_set_adminrole_nopermissions():
    embed = discord.Embed(
        title="Unable to set admin role",
        color=discord.Color.red()
    )
    embed.add_field(name="", value=f"You don't have permissions to do this!", inline=False)
    return embed

def settings_set_adminrole_success(role: discord.Role):
    embed = discord.Embed(
        title="Set Admin Role",
        color=discord.Color.green()
    )
    embed.add_field(name="", value=f"Set admin role successfully to {role.mention}", inline=False)
    return embed

def settings_set_trustedrole_nopermissions():
    embed = discord.Embed(
        title="Unable to set trusted role",
        color=discord.Color.red()
    )
    embed.add_field(name="", value=f"You don't have permissions to do this!", inline=False)
    return embed

def settings_set_trustedrole_success(role: discord.Role):
    embed = discord.Embed(
        title="Set Trusted Role",
        color=discord.Color.green()
    )
    embed.add_field(name="", value=f"Set trusted role successfully to {role.mention}", inline=False)
    return embed

def get_response(user_input: str) -> str:
    if not (user_input[0] == "!"):
        return ""
    user_input = user_input[1:]
    if (user_input == "roll a dice"):
        return f"You've rolled {randint(1, 6)}"
    return ""

def get_embed(user_input: str) -> discord.Embed:
    if not (user_input[0] == "!"):
        return None
    user_input = user_input[1:]
    if (user_input == "example embed"):
        embed = discord.Embed(
            title="Example Embed",
            description="This is a simple embed message.",
            color=discord.Color.blue()
        )
        embed.add_field(name="Field 1", value="This is the first field", inline=False)
        embed.add_field(name="Field 2", value="This is the second field", inline=True)
        embed.set_footer(text="This is a footer")

        return embed
    return None
