import asyncio
import json
import discord
import requests
from client import raidBot
from emojis import class_spec_emojis, weekday_emojis
from intl import classes_intl, specs_intl, weekdays_intl


class Question:
    def __init__(self, field_name, question, answer_reactions=None, multiple_choice=False, answer_type=str, depends_on=None):
        self.field_name = field_name
        self.question = question
        self.answer_reactions = answer_reactions or []  # do not move [] into parameter default, because it would always be the same instance
        self.answer_type = answer_type
        self.multiple_choice = multiple_choice

        self.depends_on = depends_on

        self.value = None


    async def ask(self, user):
        # templating for questions with dependencies
        ctx = {}
        if self.depends_on is not None:
            for dep in self.depends_on:
                ctx[dep.field_name] = dep.value

        question = self.question.format(**ctx)
        answer_reactions = self.answer_reactions
        if callable(answer_reactions):
            answer_reactions = answer_reactions(**ctx)

        print(f'{self.field_name}.ask()')
        # create and send message to user
        reaction_tasks = []
        message = await user.send(question)
        for reaction in answer_reactions:
            if type(reaction) == str:
                reaction_tasks.append(asyncio.create_task(message.add_reaction(reaction)))
            else:
                reaction_tasks.append(asyncio.create_task(message.add_reaction(raidBot.get_emoji(reaction))))
        if self.multiple_choice:
            reaction_tasks.append(asyncio.create_task(message.add_reaction('✅')))

        # await expected type of answer

        # without answer_reactions we expect a text message response in the channel we sent the message above
        if not len(answer_reactions):
            def check_message(m):
                return m.channel == message.channel and m.author == user

            response = await raidBot.wait_for('message', check=check_message)
            self.value = response.content
        # with answer_reactions we listen for an added reaction on the question
        else:
            def check_reaction(r, u):
                return r.message == message and u == user

            if self.multiple_choice:
                self.value = []
                while True:
                    reaction, _ = await raidBot.wait_for('reaction_add', check=check_reaction)
                    if reaction.emoji == "✅":
                        break
                    elif reaction.emoji in answer_reactions.keys():  # handle unicode emojis
                        self.value.append(answer_reactions[reaction])
                    elif reaction.emoji.id in answer_reactions.keys():  # handle custom emojis
                        self.value.append(answer_reactions[reaction.emoji.id])
            else:
                while True:
                    reaction, _ = await raidBot.wait_for('reaction_add', check=check_reaction)
                    if reaction.emoji in answer_reactions.keys():
                        self.value = answer_reactions[reaction.emoji]
                        break
                    elif reaction.emoji.id in answer_reactions.keys():
                        self.value = answer_reactions[reaction.emoji.id]
                        break


class Character:
    def __init__(self, user_id):
        self.user_id = user_id

        name = Question('name', 'Wie heißt dein Character, den du anmelden möchtest?')

        cclass = Question('cclass',
                          'Bitte wähle nun die Klasse deines Characters aus.',
                          answer_reactions={
                              emoji[0]: cclass for cclass, emoji in class_spec_emojis.items()
                          })

        spec = Question('spec',
                        'Welche Spezialisierung hast du für deinen {cclass} gewählt?',
                        answer_reactions=lambda cclass: {
                            emoji: spec for spec, emoji in class_spec_emojis[cclass][1].items()
                        },
                        depends_on=[cclass])

        rlead = Question('rlead',
                         'Traust du dir zu Raids zu leiten?',
                         answer_reactions={
                             '✅': True,
                             '❎': False
                         },
                         answer_type=bool)

        # more_days = Question('more_days',
        #     'Bist du bereit generell an einem weiteren Tag zu raiden?',
        #     answer_reactions={
        #         '✅': True,
        #         '❎': False
        #     },
        #     answer_type=bool )

        weekdays = Question('weekdays',
                            'An welchen Tagen hast du nächste Raid-ID Zeit zum Raiden? \n' + \
                            'Clicke die entsprechenden Wochentage an und danach auf das Häkchen um deine Auswahl zu bestätigen.',
                            answer_reactions=weekday_emojis,
                            multiple_choice=True
                            )

        self.confirmation_question = Question('confirmation',
                                              'Sind die Angaben für diesen Character richtig?',
                                              answer_reactions={
                                                  '✅': True,
                                                  '❎': False
                                              },
                                              answer_type=bool)

        self.edit_question = Question('edit',
                                      'Welche Frage würdest du gerne nocheinmal beantworten? \n\n```' + \
                                      '1: Charactername \n' + \
                                      '2: Klasse und Spezialisierung \n' + \
                                      '3: Raidleitung\n' + \
                                      '4: Wochentage\n' + \
                                      '5: keine, war doch alles richtig```\n' + \
                                      'Schreib mir die entsprechende Zahl.'
                                      )

        self.questions = {
            'name': name,
            'cclass': cclass,
            'spec': spec,
            'rlead': rlead,
            #     'more_days': more_days,
            'weekdays': weekdays
        }

        self.confirmed = False


    def create_embed(self):
        embed = discord.Embed(
            title=classes_intl[self.questions['cclass'].value],
            description=specs_intl[self.questions['spec'].value],
            color=0x00ff40
        )
        embed.set_author(name=self.questions['name'].value,
                         icon_url=f'https://cdn.discordapp.com/emojis/{class_spec_emojis[self.questions["cclass"].value][0]}.png'
                         )
        # w2r = "Nein"
        # if self.questions['more_days'].value: w2r = "Ja"
        # embed.add_field(name="Würde 2x raiden: ", value=w2r, inline=True)
        rl = "Nein"
        if self.questions['rlead'].value: rl = "Ja"
        embed.add_field(name="Kann Raids leiten: ", value=rl, inline=True)
        wds = ", ".join([weekdays_intl[wd] for wd in self.questions['weekdays'].value])
        embed.add_field(name="Verfügbar am:", value=wds)
        return embed


    async def start_conversation(self):
        user = raidBot.get_user(self.user_id)

        await user.send(f'Hallo {user.name}! \nDu kannst alle Antworten die du gibst am Ende nocheinmal ansehen und ändern.')

        for question in self.questions.values():
            await question.ask(user)

        while not self.confirmation_question.value:
            await user.send(embed=self.create_embed())

            await self.confirmation_question.ask(user)
            if not self.confirmation_question.value:
                await self.edit_question.ask(user)

                edit_answer = self.edit_question.value
                if edit_answer == "1":
                    await self.questions['name'].ask(user)

                elif edit_answer == "2":
                    await self.questions['cclass'].ask(user)
                    await self.questions['spec'].ask(user)

                elif edit_answer == "3":
                    await self.questions['rlead'].ask(user)

                elif edit_answer == "4":
                    await self.questions['weekdays'].ask(user)
        
        wd_map = {
            "mo": "6",
            "di": "7",
            "mi": "1",
            "do": "2",
            "fr": "3",
            "sa": "4",
            "so": "5"
        }
        character_api_model = {
            "name": self.questions['name'].value.capitalize(),
            "characterClass": self.questions['cclass'].value,
            "spec": self.questions['spec'].value,
            "raidLead": self.questions['rlead'].value,
            "possibleDaysToRaid": [wd_map[wd] for wd in self.questions['weekdays'].value],
            "favoredItems": []
        }

        print(json.dumps(character_api_model))
        response = requests.post('http://localhost:8080/characters/create', json=character_api_model)
        if(response.status_code == 200):
            await user.send("Vielen Dank, ich hab alles notiert.")
        else:
            await user.send("Da ist etwas schiefgelaufen... bitte sag Icekekw oder Syrana bescheid.")

        print('end of conversation')
        for q in self.questions.values():
            print(f'{q.field_name}: {q.value}')
