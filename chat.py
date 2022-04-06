import re 
import random
# Source code for nltk.chat.util
class Chat:
    def __init__(self, pairs, reflections={}):
        """
        Initialize the chatbot.  Pairs is a list of patterns and responses.  Each
        pattern is a regular expression matching the user's statement or question,
        e.g. r'I like (.*)'.  For each such pattern a list of possible responses
        is given, e.g. ['Why do you like %1', 'Did you ever dislike %1'].  Material
        which is matched by parenthesized sections of the patterns (e.g. .*) is mapped to
        the numbered positions in the responses, e.g. %1.

        :type pairs: list of tuple
        :param pairs: The patterns and responses
        :type reflections: dict
        :param reflections: A mapping between first and second person expressions
        :rtype: None
        """

        self._pairs = [(re.compile(x, re.IGNORECASE), y) for (x, y) in pairs]
        self._reflections = reflections
        self._regex = self._compile_reflections()

    def _compile_reflections(self):
        sorted_refl = sorted(self._reflections, key=len, reverse=True)
        return re.compile(
            r"\b({0})\b".format("|".join(map(re.escape, sorted_refl))), re.IGNORECASE
        )

    def _substitute(self, str):
        """
        Substitute words in the string, according to the specified reflections,
        e.g. "I'm" -> "you are"

        :type str: str
        :param str: The string to be mapped
        :rtype: str
        """

        return self._regex.sub(
            lambda mo: self._reflections[mo.string[mo.start() : mo.end()]], str.lower()
        )

    def _wildcards(self, response, match):
        pos = response.find("%")
        while pos >= 0:
            num = int(response[pos + 1 : pos + 2])
            response = (
                response[:pos]
                + self._substitute(match.group(num))
                + response[pos + 2 :]
            )
            pos = response.find("%")
        return response
    def respond(self, str):
        """
        Generate a response to the user input.

        :type str: str
        :param str: The string to be mapped
        :rtype: str
        """

        # check each pattern
        for (pattern, response) in self._pairs:
            match = pattern.match(str)

            # did the pattern match?
            if match:
                resp = random.choice(response)  # pick a random response
                resp = self._wildcards(resp, match)  # process wildcards

                # fix munged punctuation at the end
                if resp[-2:] == "?.":
                    resp = resp[:-2] + "."
                if resp[-2:] == "??":
                    resp = resp[:-2] + "?"
                return resp

    def converse(self, userText):
        user_input = ""
        while user_input != quit:
            user_input = quit
            try:
                user_input = userText
            except EOFError:
                print(user_input)
            if user_input:
                while user_input[-1] in "!.":
                    user_input = user_input[:-1]
                return(self.respond(user_input))

reflections = {
  "i am"       : "you are",
  "i was"      : "you were",
  "i"          : "you",
  "i'm"        : "you are",
  "i'd"        : "you would",
  "i've"       : "you have",
  "i'll"       : "you will",
  "my"         : "your",
  "you are"    : "I am",
  "you were"   : "I was",
  "you've"     : "I have",
  "you'll"     : "I will",
  "your"       : "my",
  "yours"      : "mine",
  "you"        : "me",
  "me"         : "you"
}
my_dummy_reflections= {
    "go"     : "gone",
    "hello"    : "hey there"
}
pairs = [
    [
        r"my name is (.*)",
        ["Hello %1, How are you today ?",]
    ],
     [
        r"what is your name ?",
        ["My name is Vanitha and I'm a chatbot ?",]
    ],
    [
        r"how are you ?",
        ["I'm doing good\nHow about You ?",]
    ],
    [
        r"sorry (.*)",
        ["Its alright","Its OK, never mind",]
    ],
    [
        r"i'm (.*) doing good",
        ["Nice to hear that","Alright :)",]
    ],
    [
        r"hi|hey|hello",
        ["Hello", "Hey there",]
    ],
    [
        r"(.*) age?",
        ["I'm a computer program dude\nSeriously you are asking me this?",]

    ],
    [
        r"(.*) created you?",
        ["Hemanth created me using Python's NLTK library ","top secret ;)",]
    ],
   
        [
            r"(.*) login?",
            ["login with your employee credentials given to you by your branch"]
        ],
        [
            r"(.*) customer registration?",
            ["Only executive employee can create customer registration, go to customer management dropdown menu on nav bar and click on customer regestration"]
        ],
        [
            r"(.*) update customer details?",
            ["Only executive employee can update customer details, go to customer management dropdown menu on nav bar and click on update customer details"]
        ],
        [
            r"(.*) delete customer?",
            ["Only executive employee can delete customer details, go to customer management dropdown menu on nav bar and click on update customer details"]
        ],
        [
            r"(.*) account regestration?",
            ["Only executive employee can create account, go to Account management dropdown menu on nav bar and click on account registration"]
        ],
        [
            r"(.*) delete account?",
            ["Only executive employee can delete account, go to customer management dropdown menu on nav bar and click on Delete account"]
        ],
        [
            r"(.*) customer status?",
            ["Only executive employee can view customer details, go to status details dropdown menu on nav bar and click on customer status"]

        ],
        [
            r"(.*) account status?",
            ["go to status details dropdown menu on nav bar and click on account status"]
        ],
        [
            r"(.*) customer search?",
            ["Only executive can access it,Click on search at nav bar and search with customer id or SSN id"]

        ],
        [
            r"(.*) account search?",
            ["Only cashier can access it,Click on search at nav bar and search with customer id or account id"]

        ],
        [
            r"(.*) account statement?",
            ["Only cashier can access it, Click on Account statement at nav bar"]
        ],
               [
            r"(.*) account statement?",
            ["Only cashier can access it, Click on Account statement at nav bar"]
        ],
        [
            r"(.*) Deposit?",
            ["Only cashier can access it, Click on account details and enter account id submit then select deposit button "]
        ],
                [
            r"(.*) withdraw?",
            ["Only cashier can access it, Click on account details and enter account id submit then select withdraw button "]
        ],
              [
            r"(.*) Transfer?",
            ["Only cashier can access it, Click on account details and enter account id submit then select Transfer button "]
        ],

    [
        r"quit",
        ["BBye take care. See you soon :) ","It was nice talking to you. See you soon :)"]

],
]

def vanitha(userText):
    chat = Chat(pairs, reflections)
    return chat.converse(userText)


