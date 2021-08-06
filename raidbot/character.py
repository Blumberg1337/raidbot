import discord
from client import raidBot
from emojis import class_spec_emojis

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
        print(f'{self.field_name}.ask()')
        # create and send message to user
        message = await user.send(self.question)
        for reaction in self.answer_reactions:
            await message.add_reaction(raidBot.get_emoji(reaction))
        if self.multiple_choice:
            await message.add_reaction('✅')

        # await expected type of answer

        # without answer_reactions we expect a text message response in the channel we sent the message above
        if not len(self.answer_reactions):
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
                    if reaction.emoji.id in self.answer_reactions.keys(): # handle custom emojis
                        self.value.append(self.answer_reactions[reaction.id])
                    elif reaction.emoji in self.answer_reactions.keys(): # handle unicode emojis
                        self.value.append(self.answer_reactions[reaction])
            else:
                while True: # this sucks
                    reaction, _ = await raidBot.wait_for('reaction_add', check=check_reaction)
                    if reaction.emoji.id in self.answer_reactions.keys():
                        self.value = self.answer_reactions[reaction.emoji.id]
                        break
                    elif reaction.emoji in self.answer_reactions.keys():
                        self.value = self.answer_reactions[reaction.emoji]



class Character:
    def __init__(self, user_id):
        self.user_id = user_id

        name = Question('name', 'Wie heißt dein Character, den du anmelden möchtest?')

        cclass = Question('class', 
            'Bitte wähle nun die Klasse deines Characters aus.', 
            answer_reactions={ 
                emoji[0]:cclass for cclass, emoji in class_spec_emojis.items() 
            })

        spec = Question('spec', 
            'Welche Spezialisierung hast du für deinen Character gewählt?',
            answer_reactions=lambda cls: {
                emoji:spec for spec, emoji in class_spec_emojis[cls][1].items()
            },
            depends_on=cclass )

        self.questions = [
            name, cclass, spec
        ]

        self.confirmed = False
    

    async def start_conversation(self):
        user = raidBot.get_user(self.user_id)

        await user.send(f'Hallo {user.name}! \n Du kannst alle Antworten die du gibst am Ende nocheinmal ansehen und ändern.')

        for question in self.questions:
            await question.ask(user)

        print('end of conversation')
        for q in self.questions:
            print(f'{q.field_name}: {q.value}')
