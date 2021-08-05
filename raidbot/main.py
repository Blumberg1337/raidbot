import os
from enum import Enum
import discord
import requests
from discord.ext import commands

LOCAL_ENV_TESTING = os.getenv("LOCAL_ENV_TESTING")
raidBot = commands.Bot(command_prefix="_", intents=discord.Intents.all())
raidApplicants = {}
check_mark = "✅"
cross_mark = "❎"
wink = "😉"
emoji_server_id = "561216209333256216"
emoji_list = {
    "druid": [863593609243394088, {
        "balance": 863593609177071656,
        "feral": 863593608909553705,
        "tank": 863593609211019284,
        "restoration": 863593609340387339,
    }],
    "hunter": [863593661206888529, {
        "beast_mastery": 863593661081321513,
        "marksmanship": 863593661102030859,
        "survival": 863593661404151818,
    }],
    "mage": [863593695390990346, {
        "arcane": 863593695261622272,
        "fire": 863593695294521374,
        "frost": 863593695411306506,
    }],
    "paladin": [863593727351455764, {
        "holy": 863593727163629588,
        "protection": 863593727183814696,
        "retribution": 863593727343722546,
    }],
    "priest": [863593923649601537, {
        "discipline": 863593924010180608,
        "holy": 863593727163629588,
        "shadow": 863593924090396702,
    }],
    "rogue": [863593969086234654, {
        "assassination": 863593969070112778,
        "combat": 863593969057529856,
        "subtlety": 863593969074438175,
    }],
    "shaman": [863593572132585513, {
        "elemental": 863539342681178112,
        "enhancement": 863539342689828904,
        "restoration": 863539342375125023,
    }],
    "warlock": [863594114879717386, {
        "affliction": 863594114901999625,
        "demonology": 863594114821652494,
        "destruction": 863594114980905000,
    }],
    "warrior": [863594161084039178, {
        "arms": 863594161046552617,
        "fury": 863594161130176552,
        "protection": 863594160909320213,
    }],
}

classes_intl = {
    "druid": "Druide",
    "hunter": "Jäger",
    "mage": "Magier",
    "paladin": "Paladin",
    "priest": "Priester",
    "rogue": "Schurke",
    "shaman": "Schamane",
    "warlock": "Hexenmeister",
    "warrior": "Krieger",
}

specs_intl = {
    "balance": "Gleichgewicht",
    "feral": "Wilder Kampf (Katze)",
    "tank": "Wilder Kampf (Tank)",
    "restoration": "Wiederherstellung",
    "beast_mastery": "Tierherrschaft",
    "marksmanship": "Treffsicherheit",
    "survival": "Überleben",
    "arcane": "Arkan",
    "fire": "Feuer",
    "frost": "Frost",
    "holy": "Heilig",
    "protection": "Schutz",
    "retribution": "Vergeltung",
    "discipline": "Disziplin",
    "shadow": "Schatten",
    "assassination": "Meucheln",
    "combat": "Kampf",
    "subtlety": "Täuschung",
    "elemental": "Elementar",
    "enhancement": "Verstärkung",
    "affliction": "Gebrechen",
    "demonology": "Dämonologie",
    "destruction": "Zerstörung",
    "arms": "Waffen",
    "fury": "Furor",
}


def is_bot(user: discord.User):
    return user == raidBot.user


class UserState(Enum):
    waiting_for_character_name = 0
    waiting_for_character_name_confirmation = 1
    waiting_for_character_class = 2
    waiting_for_character_class_confirmation = 3
    waiting_for_character_spec = 4
    waiting_for_character_spec_confirmation = 5
    waiting_for_character_raidlead = 6
    waiting_for_character_additional_day_to_raid = 7
    waiting_for_character_favored_items = 8
    waiting_for_character_favored_items_confirmation = 9
    waiting_for_user_possible_days_to_raid = 10
    waiting_for_user_possible_days_to_raid_confirmation = 11


@raidBot.event
async def on_ready():
    print("started")
    # for _ in emoji_list.items():
    #     vals = _[1][1].values()
    #     print(_)
    #     print(_[0])
    #     print(_[1])
    #     print(_[1][0])
    #     print(_[1][1])
    #     print(vals)
    #     for v in vals:
    #         print(v)
    if not LOCAL_ENV_TESTING:
        print("You are not testing locally!\n" + "LOCAL_ENV_TESTING set to " + str(LOCAL_ENV_TESTING))
        channel = raidBot.get_channel(863573906354864178)
    else:
        print("You are testing locally!\n" + "LOCAL_ENV_TESTING set to " + str(LOCAL_ENV_TESTING))
        channel = raidBot.get_channel(865929233267556363)
        # msg = await channel.fetch_message(channel.last_message_id)
        msg = await channel.fetch_message(868520109969391657)
        embdict = msg.embeds[0].to_dict()
        print(embdict)
        for key, value in embdict.items():
            if key == "fields":
                print(key)
                for fval in embdict["fields"]:
                    print(fval)
            else:
                print(key, ": ", value)
        await channel.send("**LOCAL_ENV_TESTING mode " + LOCAL_ENV_TESTING + "!**")
    welcome_message = await channel.send("Hallo, ich bin der RAID-Bot und helfe bei der Zusammenstellung von Raid-Gruppen.\n"
                                         "**Hast du Zeit und Lust an unseren Raids teilzunehmen?**\n"
                                         "Wenn ja, klicke einfach auf den grünen Haken.\n"
                                         "Ich schreibe dir dann. " + wink)
    await welcome_message.add_reaction(check_mark)


@raidBot.event
async def on_reaction_add(reaction: discord.Reaction, user: discord.User):
    if is_bot(user):
        return

    message = ""
    reactions = []
    character_name_question = "**Wie heißt dein Charakter, den du anmelden möchtest?**"
    class_choice = "**Bitte wähle nun die Klasse deines Charakters aus.**"
    spec_choice = "**Welche Spezialisierung hast du mit deinem Charakter gewählt?**"
    raidlead_choice = "Traust du dir zu **Raids zu leiten**?"
    additional_day_to_raid_choice = "Bist du bereit generell **an einem weiteren Tag** zu raiden?"
    days_to_raid_question = "**An welchen Tagen hast du übernächste Raid-ID Zeit zum Raiden?**\n" \
                            "Bitte gib in deiner Antwort deutsche Wochentage oder die dafür gängigen Abkürzungen (Mo, Di, ...) ein. "
    # start interaction with user
    if reaction.emoji == check_mark:
        # save user on first interaction
        if user.id not in raidApplicants or "state" not in raidApplicants[user.id]:
            raidApplicants[user.id] = {"state": UserState.waiting_for_character_name}
            print("state bound to this user:", raidApplicants[user.id]["state"].name)
            # greet user on first interaction
            if "name" not in raidApplicants[user.id]:
                user_greeting = "Hallo " + "**" + user.name + "#" + user.discriminator + "**!\n\n"
                # requesting character name
                message = user_greeting + character_name_question
            print(str(raidApplicants.keys()) + " reacted")
    # creating dm channel on first reaction
    dm_channel: discord.DMChannel = user.dm_channel
    if dm_channel is None and not user.bot:
        dm_channel = await user.create_dm()
    # do nothing if reaction is not made on last_message
    if user.id not in raidApplicants:
        return
    if "lastMessageId" in raidApplicants[user.id] and raidApplicants[user.id]["lastMessageId"] != reaction.message.id:
        return
    # user reacts with cross mark
    if reaction.emoji == cross_mark:
        # change state for wrong character name
        if raidApplicants[user.id]["state"] == UserState.waiting_for_character_name_confirmation:
            raidApplicants[user.id]["state"] = UserState.waiting_for_character_name
            # requesting character name
            message = character_name_question
        # change state for wrong character class
        elif raidApplicants[user.id]["state"] == UserState.waiting_for_character_class_confirmation:
            raidApplicants[user.id]["state"] = UserState.waiting_for_character_class
            # requesting character class
            message = class_choice
            for character_class in emoji_list.values():
                reactions.append(raidBot.get_emoji(character_class[0]))
        # change state for wrong spec
        elif raidApplicants[user.id]["state"] == UserState.waiting_for_character_spec_confirmation:
            raidApplicants[user.id]["state"] = UserState.waiting_for_character_spec
            # requesting spec
            message = spec_choice
            for spec_emoji_id in emoji_list[raidApplicants[user.id]["characterClass"]][1].values():
                reactions.append(raidBot.get_emoji(spec_emoji_id))
        # saving raidlead (false)
        elif raidApplicants[user.id]["state"] == UserState.waiting_for_character_raidlead:
            raidApplicants[user.id]["state"] = UserState.waiting_for_character_additional_day_to_raid
            raidApplicants[user.id]["raidLead"] = False
            print(str(raidApplicants) + " raidlead(s) stored")
            message = additional_day_to_raid_choice
            reactions.append(check_mark)
            reactions.append(cross_mark)
        # saving additional_day_to_raid (false)
        elif raidApplicants[user.id]["state"] == UserState.waiting_for_character_additional_day_to_raid:
            raidApplicants[user.id]["state"] = UserState.waiting_for_user_possible_days_to_raid
            raidApplicants[user.id]["additionalDayToRaid"] = False
            print(str(raidApplicants) + " additional_day(s)_to_raid stored")
            message = days_to_raid_question
    # user reacts with check mark
    elif reaction.emoji == check_mark:
        # user confirmed character name
        if raidApplicants[user.id]["state"] == UserState.waiting_for_character_name_confirmation:
            raidApplicants[user.id]["state"] = UserState.waiting_for_character_class
            message = await dm_channel.send("Ich habe den Charakternamen **" + raidApplicants[user.id]["name"] + "** gespeichert.\nDu kannst den Charakternamen später noch anpassen.")
        # requesting character class
        if raidApplicants[user.id]["state"] == UserState.waiting_for_character_class:
            message = class_choice
            for character_class in emoji_list.values():
                reactions.append(raidBot.get_emoji(character_class[0]))
        # user confirmed character class
        elif raidApplicants[user.id]["state"] == UserState.waiting_for_character_class_confirmation:
            raidApplicants[user.id]["state"] = UserState.waiting_for_character_spec
            message = "Deine Klasse **" + classes_intl[raidApplicants[user.id]["characterClass"]] + "** ist jetzt gespeichert.\nDu kannst deine Klasse später noch anpassen."
        # requesting spec
        if raidApplicants[user.id]["state"] == UserState.waiting_for_character_spec:
            message = spec_choice
            for spec_emoji_id in emoji_list[raidApplicants[user.id]["characterClass"]][1].values():
                reactions.append(raidBot.get_emoji(spec_emoji_id))
        # user confirmed spec
        elif raidApplicants[user.id]["state"] == UserState.waiting_for_character_spec_confirmation:
            raidApplicants[user.id]["state"] = UserState.waiting_for_character_raidlead
            message = "Ich habe für deine Klasse **" + classes_intl[raidApplicants[user.id]["characterClass"]] + \
                        "** die Spezialisierung **" + specs_intl[raidApplicants[user.id]["spec"]] + \
                        "** hinterlegt.\nSpäter hast du die Möglichkeit deine Spezialisierung anzupassen.\n" + raidlead_choice
            reactions.append(check_mark)
            reactions.append(cross_mark)
        # saving raidlead (true)
        elif raidApplicants[user.id]["state"] == UserState.waiting_for_character_raidlead:
            raidApplicants[user.id]["state"] = UserState.waiting_for_character_additional_day_to_raid
            raidApplicants[user.id]["raidLead"] = True
            print(str(raidApplicants) + " raidlead(s) stored")
            message = additional_day_to_raid_choice
            reactions.append(check_mark)
            reactions.append(cross_mark)
        # saving additional_day_to_raid (true)
        elif raidApplicants[user.id]["state"] == UserState.waiting_for_character_additional_day_to_raid:
            raidApplicants[user.id]["state"] = UserState.waiting_for_user_possible_days_to_raid
            raidApplicants[user.id]["additionalDayToRaid"] = True
            print(str(raidApplicants) + " additional_day(s)_to_raid stored")
            message = days_to_raid_question
    if raidApplicants[user.id]["state"] == UserState.waiting_for_character_class:
        for character_class_key, character_class_value in emoji_list.items():
            class_emoji_id = character_class_value[0]
            if isinstance(reaction.emoji, discord.Emoji) and reaction.emoji.id == class_emoji_id:
                message = "Soll ich **" + classes_intl[character_class_key] + "** für deinen Charakter speichern?"
                # saving character class
                raidApplicants[user.id]["characterClass"] = character_class_key
                # raidApplicants[user.id]["characterClass"] = {"key": character_class_key,
                #                                              "name": character_class_value}
                print(str(raidApplicants) + " class(es) stored")
                raidApplicants[user.id]["state"] = UserState.waiting_for_character_class_confirmation
                reactions.append(check_mark)
                reactions.append(cross_mark)
    elif raidApplicants[user.id]["state"] == UserState.waiting_for_character_spec:
        for spec_key, spec_value in emoji_list[raidApplicants[user.id]["characterClass"]][1].items():
            spec_emoji_id = spec_value
            if isinstance(reaction.emoji, discord.Emoji) and reaction.emoji.id == spec_emoji_id:
                message = "Ist **" + specs_intl[spec_key] + "** für deinen Charakter richtig?"
                # saving spec
                raidApplicants[user.id]["spec"] = spec_key
                print(str(raidApplicants) + " spec(s) stored")
                raidApplicants[user.id]["state"] = UserState.waiting_for_character_spec_confirmation
                reactions.append(check_mark)
                reactions.append(cross_mark)
    # sending message to user
    if message:
        last_message = await dm_channel.send(message)
        raidApplicants[user.id]["lastMessageId"] = last_message.id
        # adding reactions to last message
        for reaction in reactions:
            await last_message.add_reaction(reaction)


@raidBot.event
async def on_message(message: discord.Message):
    if is_bot(message.author):
        return
    if not isinstance(message.channel, discord.DMChannel):
        return

    backend_error_message = "Beim Absenden deiner Daten zum Backend ist leider ein Fehler aufgetreten.\nBitte versuche es später erneut!\n\n"
    # requesting character name confirmation
    if raidApplicants[message.author.id]["state"] == UserState.waiting_for_character_name:
        character_name = message.content.capitalize()
        character_name_confirmation_message = await message.channel.send("Ich habe mir den Charakternamen **" + character_name + "** gemerkt.\nIst das korrekt?")
        # saving character name
        raidApplicants[message.author.id]["name"] = character_name
        print(str(raidApplicants) + " name(s) stored")
        raidApplicants[message.author.id]["state"] = UserState.waiting_for_character_name_confirmation
        raidApplicants[message.author.id]["lastMessageId"] = character_name_confirmation_message.id
        await character_name_confirmation_message.add_reaction(check_mark)
        await character_name_confirmation_message.add_reaction(cross_mark)
    elif raidApplicants[message.author.id]["state"] == UserState.waiting_for_user_possible_days_to_raid:
        possible_days_to_raid = message.content.lower().split(',')
        raidApplicants[message.author.id]["possibleDaysToRaid"] = possible_days_to_raid
        print(str(raidApplicants) + " possible_days_to_raid stored")
        print(str(raidApplicants[message.author.id]))
        # since requests cannot handle enums just like that we need to transform it into a string
        raidApplicants[message.author.id]["state"] = raidApplicants[message.author.id]["state"].name
        # try to send the collected data to our backend
        # noinspection PyBroadException
        try:
            raidApplicants[message.author.id]["response"] = requests.post('http://localhost:8080/characters/create', json=raidApplicants[message.author.id])
        except Exception as e:
            await message.channel.send(backend_error_message)
            raise e
        if raidApplicants[message.author.id].keys().__contains__("response"):
            print("backend response: ", str(raidApplicants[message.author.id]["response"]))
            print(str(raidApplicants[message.author.id]["response"].text))
            if raidApplicants[message.author.id]["response"].status_code == 200:
                character_data_message = ""
                for character_data in raidApplicants[message.author.id].items():
                    character_data_message += character_data[0] + ": " + str(character_data[1]) + "\n"
                await message.channel.send("**Vielen Dank** für deine Antworten und Reaktionen.\n\nHier nochmal eine Übersicht über deine Angaben:\n\n**"
                                            + character_data_message + "\n**Bis zum nächsten Mal!")
                del raidApplicants[message.author.id]
                print("raidApplicants:", str(raidApplicants))
            else:
                await message.channel.send(backend_error_message + "Backend antwortete mit Code " + str(raidApplicants[message.author.id]["response"]))


if not LOCAL_ENV_TESTING:
    raidBot.run(os.getenv("RAIDBOT_PROD_API_KEY"))
else:
    raidBot.run(os.getenv("RAIDBOT_LOCAL_API_KEY"))
