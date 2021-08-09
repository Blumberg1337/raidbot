import discord
import asyncio
from client import raidBot
from emojis import class_spec_emojis, weekday_emojis
from intl import classes_intl, specs_intl, weekdays_intl

class Question:
    def __init__(self, field_name, question, answer_reactions=None, multiple_choice=False, answer_type=str, depends_on=None):
        self.field_name       = field_name
        self.question         = question
        self.answer_reactions = answer_reactions or []  # do not move [] into parameter default, because it would always be the same instance
        self.answer_type      = answer_type
        self.multiple_choice  = multiple_choice

        self.depends_on       = depends_on

        self.value            = None

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
            def check_reaction(r,u):
                return r.message == message and u == user

            if self.multiple_choice:
                self.value = []
                while True:
                    reaction, _ = await raidBot.wait_for('reaction_add', check=check_reaction)
                    if reaction.emoji == "✅": 
                        break
                    elif reaction.emoji in answer_reactions.keys(): # handle unicode emojis
                        self.value.append(answer_reactions[reaction])
                    elif reaction.emoji.id in answer_reactions.keys(): # handle custom emojis
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
                emoji[0]:cclass for cclass, emoji in class_spec_emojis.items() 
            })

        spec = Question('spec', 
            'Welche Spezialisierung hast du für deinen {cclass} gewählt?',
            answer_reactions=lambda cclass: {
                emoji:spec for spec, emoji in class_spec_emojis[cclass][1].items()
            },
            depends_on=[cclass] )
        
        rlead = Question('rlead',
            'Traust du dir zu Raids zu leiten?',
            answer_reactions={
                '✅': True,
                '❎': False
            },
            answer_type=bool )

        # more_days = Question('more_days',
        #     'Bist du bereit generell an einem weiteren Tag zu raiden?',
        #     answer_reactions={
        #         '✅': True,
        #         '❎': False
        #     },
        #     answer_type=bool )
        
        weekdays = Question('weekdays', 
            'An welchen Tagen hast du nächste Raid-ID Zeit zum Raiden? \n'+\
            'Clicke die entsprechenden Wochentage an und danach auf das Häkchen um deine Auswahl zu bestätigen.',
            answer_reactions=weekday_emojis,
            multiple_choice=True
        )

        self.questions = {
            'name':      name, 
            'cclass':    cclass, 
            'spec':      spec, 
            'rlead':     rlead, 
        #     'more_days': more_days,
            'weekdays':  weekdays
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

        await user.send(f'Hallo {user.name}! \n Du kannst alle Antworten die du gibst am Ende nocheinmal ansehen und ändern.')

        for question in self.questions.values():
            await question.ask(user)
        
        await user.send(embed=self.create_embed())

        print('end of conversation')
        for q in self.questions.values():
            print(f'{q.field_name}: {q.value}')
