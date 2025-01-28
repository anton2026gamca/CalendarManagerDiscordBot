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
            if (visible):
                embed.add_field(name="", value=f":white_small_square: **{subject}** - **{type}** - {name}\nㅤㅤ`{date}`ㅤ(id: `{id}`)`", inline=False)
                num_events += 1
    if (num_events == 0):
        embed.add_field(name="", value="You dont have any events", inline=False)
    else:
        embed.add_field(name="", value="Use `/event info [event id]` for more info", inline=False)
    return embed

def event_on_date(server_id: int, user_roles: discord.Role, day: int, month: int, year: int) -> discord.Embed:
    embed = discord.Embed(
        title=f"Events on {day}.{month}. {year}",
        color=discord.Color.blue()
    )
    num_events: int = 0
    if calendars.get(str(server_id)) is not None:
        for event in calendars[str(server_id)].get("events", []):
            event_type: str = event["type"]
            event_name: str = event["name"]
            event_subject: str = event["subject"]
            event_day: int = event["day"]
            event_month: int = event["month"]
            event_year: int = event["year"]
            event_date: str = f"{event_day}.{event_month}. {event_year}"
            event_id: int = event["id"]
            visible = False
            # Check if subjects role is in user roles 
            if subjects.get(f"{server_id}", []) is not None:
                for s in subjects[f"{server_id}"]["subjects"]:
                    if s["name"] == event_subject:
                        for role in user_roles:
                            if role.id == s["role_id"]:
                                visible = True
            # Check if event is on date
            if visible and not (event_day == day and event_month == month and event_year == year):
                visible = False
            if (visible):
                embed.add_field(name="", value=f":white_small_square: **{event_subject}** - **{event_type}** - {event_name}\nㅤㅤ`{event_date}`ㅤ(id: `{event_id}`)`", inline=False)
                num_events += 1
    if (num_events == 0):
        embed.add_field(name="", value="*** *cricket noise* ***", inline=False)
    else:
        embed.add_field(name="", value="Use `/event info [event id]` for more info", inline=False)
    return embed

def ivalid_date(day: int, month: int, year: int) -> discord.Embed:
    embed = discord.Embed(
        title=f"Invalid date!",
        color=discord.Color.red()
    )
    embed.add_field(name="", value=f"Date \"{day}.{month}. {year}\" is invalid!", inline=False)
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
    text: str = get_subjects_text(server_id, user_roles, subjects, False)
    embed.add_field(name="Subjects you can use:", value=text, inline=False)
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
    text: str = get_subjects_text(server_id, user_roles, subjects, False)
    embed.add_field(name="Subjects you can use:", value=text, inline=False)
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
    if not is_date_valid(day, month, year):
        return ivalid_date(day, month, year)
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
    embed.add_field(name="", value=f"Subject \"{subject}\" already exists!", inline=False)
    return embed

def add_subject_nopermissions() -> discord.Embed:
    embed = discord.Embed(
        title="Failed to add subject",
        color=discord.Color.red()
    )
    embed.add_field(name="", value=f"You MUST be the server owner to do this!", inline=False)
    return embed

def add_subject_success(subject: str, role: discord.Role, channel: discord.TextChannel | None) -> discord.Embed:
    embed = discord.Embed(
        title="Added Subject Successfully",
        color=discord.Color.green()
    )
    embed.add_field(name="", value=f"Subject: {subject}", inline=False)
    embed.add_field(name="", value=f"Role: {role.mention}", inline=False)
    if channel is not None:
        embed.add_field(name="", value=f"Channel: {channel.mention}", inline=False)
    return embed

def edit_subject_nopermissions() -> discord.Embed:
    embed = discord.Embed(
        title="Failed to edit subject",
        color=discord.Color.red()
    )
    embed.add_field(name="", value=f"You MUST be the server owner to do this!", inline=False)
    return embed

def edit_subject_doesnotexist(subject_name: str) -> discord.Embed:
    embed = discord.Embed(
        title="Failed to edit subject",
        color=discord.Color.red()
    )
    embed.add_field(name="", value=f"Subject with name \"{subject_name}\" does not exist!", inline=False)
    return embed

def edit_subject_success(old_name: str, new_name: str, old_role_id: int, new_role_id: int, old_channel_id: int, new_channel_id: int) -> discord.Embed:
    embed = discord.Embed(
        title="Changed Subject Successfully",
        color=discord.Color.green()
    )
    changes: int = 0
    if (new_name != old_name):
        embed.add_field(name="", value=f"Name: \"{old_name}\" -> \"{new_name}\"", inline=False)
        changes += 1
    if (new_role_id != old_role_id):
        embed.add_field(name="", value=f"Role: <@&{old_role_id}> -> <@&{new_role_id}>", inline=False)
        changes += 1
    if (new_channel_id != old_channel_id and (new_channel_id >= 0 or old_channel_id >= 0)):
        new_channel: str = f"<#{new_channel_id}>" if new_channel_id >= 0 else "None"
        old_channel: str = f"<#{old_channel_id}>" if old_channel_id >= 0 else "None"
        embed.add_field(name="", value=f"Channel: {old_channel} -> {new_channel}", inline=False)
        changes += 1
    if (changes <= 0):
        embed.add_field(name="", value=f"There were no changes made to the subject", inline=False)
    return embed

def remove_subject_nopermissions() -> discord.Embed:
    embed = discord.Embed(
        title="Failed to remove subject",
        color=discord.Color.red()
    )
    embed.add_field(name="", value=f"You MUST be the server owner to do this!", inline=False)
    return embed

def remove_subject_doesnotexist(subject_name: str) -> discord.Embed:
    embed = discord.Embed(
        title="Failed to remove subject",
        color=discord.Color.red()
    )
    embed.add_field(name="", value=f"Subject with name \"{subject_name}\" does not exist!", inline=False)
    return embed

def remove_subject_success(subject_name: str) -> discord.Embed:
    embed = discord.Embed(
        title="Remove Subject Successfully",
        color=discord.Color.green()
    )
    embed.add_field(name="", value=f"Name: \"{subject_name}\"", inline=False)
    return embed

def get_subjects_embed(server_id: int, user_roles: discord.Role, subjects) -> discord.Embed:
    embed = discord.Embed(
        title="",
        color=discord.Color.blue()
    )
    text = get_subjects_text(server_id, user_roles, subjects, False)
    embed.add_field(name="Subjects you can use:", value=text, inline=False)
    return embed

def get_all_subjects_embed(server_id: int, user_roles: discord.Role | None, subjects) -> discord.Embed:
    embed = discord.Embed(
        title="",
        color=discord.Color.blue()
    )
    text = get_subjects_text(server_id, user_roles, subjects, True)
    embed.add_field(name="All subjects:", value=text, inline=False)
    return embed

def get_subjects_text(server_id: int, user_roles: discord.Role | None, subjects, print_all: bool) -> str:
    text: str = ""
    num_subjects: int = 0
    if subjects.get(str(server_id)) is not None:
        user_roles_id = []
        if user_roles is not None:
            for role in user_roles:
                user_roles_id.append(role.id)
        i: int = 0
        for subj in subjects[str(server_id)]["subjects"]:
            can_use: bool = user_roles_id.__contains__(subj["role_id"])
            if print_all or can_use:
                emoji: str = ":white_small_square:" if subj.get("channel") is not None and subj["channel"] > -1 else ":small_blue_diamond:"
                id: str = f"({i})" if print_all else ""
                name: str = subj["name"]
                text += f"{emoji} {id} {name}\n"
                num_subjects += 1
            i += 1
    if (num_subjects == 0):
        text = "There are no subjects"
    return text

def get_subject_info_not_found(id: int):
    embed = discord.Embed(
        title="Subject Not Found",
        color=discord.Color.red()
    )
    embed.add_field(name="", value=f"Couldn't find a subject with id \"{id}\"", inline=False)
    return embed

def get_subject_info(subject):
    embed = discord.Embed(
        title="Get Subject Info",
        color=discord.Color.blue()
    )
    text: str = ""
    role_id = subject["role_id"]
    text += f"Role: <@&{role_id}>"
    if "channel" in subject:
        channel = subject["channel"]
        text += f"\nChannel: <#{channel}>"
    name = subject["name"]
    embed.add_field(name=f"Subject: {name}", value=text, inline=False)
    return embed

def set_adminrole_nopermissions():
    embed = discord.Embed(
        title="Unable to set admin role",
        color=discord.Color.red()
    )
    embed.add_field(name="", value=f"You don't have permissions to do this!", inline=False)
    return embed

def set_adminrole_success(role: discord.Role):
    embed = discord.Embed(
        title="Set Admin Role",
        color=discord.Color.green()
    )
    embed.add_field(name="", value=f"Set admin role successfully to {role.mention}", inline=False)
    return embed

def set_trustedrole_nopermissions():
    embed = discord.Embed(
        title="Unable to set trusted role",
        color=discord.Color.red()
    )
    embed.add_field(name="", value=f"You don't have permissions to do this!", inline=False)
    return embed

def set_trustedrole_success(role: discord.Role):
    embed = discord.Embed(
        title="Set Trusted Role",
        color=discord.Color.green()
    )
    embed.add_field(name="", value=f"Set trusted role successfully to {role.mention}", inline=False)
    return embed

def set_helpchannel_nopermissions():
    embed = discord.Embed(
        title="Unable to set help channel",
        color=discord.Color.red()
    )
    embed.add_field(name="", value=f"You don't have permissions to do this!", inline=False)
    return embed

def set_helpchannel_success(channel: discord.TextChannel):
    embed = discord.Embed(
        title="Set Help Channel",
        color=discord.Color.green()
    )
    embed.add_field(name="", value=f"Set help channel successfully to {channel.mention}", inline=False)
    return embed

def set_calendarcategory_nopermissions():
    embed = discord.Embed(
        title="Unable to set calendar category",
        color=discord.Color.red()
    )
    embed.add_field(name="", value=f"You don't have permissions to do this!", inline=False)
    return embed

def set_calendarcategory_success(category: discord.CategoryChannel):
    embed = discord.Embed(
        title="Set Calendar Category",
        color=discord.Color.green()
    )
    embed.add_field(name="", value=f"Set calendar category successfully to {category.mention}", inline=False)
    return embed

def get_adminrole(role_id: int | None):
    embed = discord.Embed(
        title="Get Admin Role",
        color=discord.Color.blue()
    )
    text: str = f"<@&{role_id}>" if role_id is not None else "not set, set it with `/set admin_role`"
    embed.add_field(name="", value=f"The admin role is {text}", inline=False)
    return embed

def get_trustedrole(role_id: int | None):
    embed = discord.Embed(
        title="Get Trusted Role",
        color=discord.Color.blue()
    )
    text: str = f"<@&{role_id}>" if role_id is not None else "not set, set it with `/set trusted_role`"
    embed.add_field(name="", value=f"The trusted role is {text}", inline=False)
    return embed

def get_helpchannel(channel_id: int | None):
    embed = discord.Embed(
        title="Get Help Channel",
        color=discord.Color.blue()
    )
    text: str = f"<#{channel_id}>" if channel_id is not None else "not set, set it with `/set help_channel`"
    embed.add_field(name="", value=f"The help channel is {text}", inline=False)
    return embed

def get_calendarcategory(channel_id: int | None):
    embed = discord.Embed(
        title="Get Calendar Category",
        color=discord.Color.blue()
    )
    text: str = f"<#{channel_id}>" if channel_id is not None else "not set, set it with `/set calendar_category`"
    embed.add_field(name="", value=f"The calendar category is {text}", inline=False)
    return embed

def problem_resolved(user_mention: str) -> discord.Embed:
    embed = discord.Embed(
        title="",
        color=discord.Color.blue()
    )
    embed.add_field(name="", value=f"This problem was marked as resolved by {user_mention}", inline=False)
    return embed

def get_response(user_input: str) -> str:
    if not user_input[0] == "!":
        return ""
    user_input = user_input[1:]
    return ""