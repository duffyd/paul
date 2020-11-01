import os

class Config(object):
    SQLALCHEMY_DATABASE_URI='postgresql://{}:{}@{}:{}/{}'.format(
        "paul",
        "password",
        "localhost",
        5432,
        "paul"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS=False
    SECRET_KEY=os.urandom(32)
    
INITIAL_SCORE = {
    'f': 2,
    's': 2,
    'b': 2,
    't': 0
}

CARD_TYPES = [
    ('', 'Select a Card Type'),
    ('City Quiz', 'City Quiz'),
    ('City Trial', 'City Trial'),
    ('Land Trial', 'Land Trial'),
    ('Quiz', 'Quiz'),
    ('Sea Trial', 'Sea Trial'),
]

MISSIONS = {
    '1': {'b': 5, 'c': 4, 's': 5},
    '2': {'b': 11, 'c': 2, 's': 5},
    '3': {'c': 1, 'e': 7, 's': 5}
}

B_PLACES = {
    '1': {'Paphos': 1, 'Iconium': 4},
    '2': {'Derbe': 2, 'Lystra': 2, 'Iconium': 2, 'Antioch (Pisidia)': 2, 'Athens': 3},
    '3': {'Ephesus': 3}
}

C_PLACES = {
    '1': {'Derbe': 1, 'Lystra': 1, 'Iconium': 1, 'Antioch (Pisidia)': 1},
    '2': {'Philippi': 1, 'Corinth': 1},
    '3': {'Ephesus': 1}
}

E_PLACES = {
    '3': {'Jerusalem': 7}
}

RULES = """**Basic game workflow is:**

1. Roll dice <i class="material-icons">pan_tool</i>
2. Place resource: Believer <i class="material-icons">person</i>, Elder <i class="material-icons">supervisor_account</i>, or Congregation <i class="material-icons">home</i>
3. Next player <i class="material-icons">transfer_within_a_station</i>

**Detailed rules:**

* Pick which missionary tour - 1, 2 or 3
* At the beginning you receive 2 believers, 2 food, 2 money resources
* You have to complete all missions for your selected missionary tour
* On your turn you throw the dice and your player moves the number of places on the dice. Depending on where you land you either face a land/sea trial or have a pop quiz. These are randomly selected
* Places have associated trials & pop quizzes. If you guess a pop quiz correctly, you receive 1 believer. If you can’t guess, there are no penalties
* 2 believers equals 1 elder
* At the end of your turn, you may place any resources, i.e. believers, congregations, or elders. You have to have completed 1 tour circuit prior to doing this. To place a congregation, you must have 3 believers
* You always need 1 food, and 1 money resource. If not, it is game over
* When you pass Antioch (Syria), you get 1 food and 1 money
* If you land on Tarsus or Paphos, you also get 1 food & 1 money"""

MISSIONS_TEXT = {
    '1': """1. **Place 1 believer on Paphos** *(Sergius Paulus, proconsul of Cyprus, becomes a believer (Acts 13:7, 12))*
2. **Place 4 believers on Iconium** *(“A great multitude of both Jews and Greeks became believers” (Acts 14:1))*
3. **Place 1 congregation on Derbe** *(In Derbe, Paul and Barnabas help quite a few to become disciples; form a small group/congregation (Ac 14:20b, 21a))*
4. **Place 1 congregation on Lystra, Iconium, and Antioch (Pisidia)** *(Form congregations in Lystra, Iconium, and Antioch (Acts 14:21, 22))*
5. **Get 5 silver**""",
    '2': """1. **Place 2 believers on Derbe, Lystra, Iconium, and Antioch (of Pisidia)** *(Visited and encouraged congregations and as a result they were made firm in the faith and increased in size (Acts 16:5))*
2. **Place 1 congregation on Philippi** *(At Philippi, Paul witnesses to Lydia and her and her household get baptised (Acts 16:13-15); the jailer and his household get baptised (Acts 16:31-33))*
3. **Place 3 believers on Athens** *(Some became believers in Athens (Acts 17:34))*
4. **Place 1 congregation on Corinth** *(Paul forms a congregation in Corinth (Acts 18:8))*
5. **Get 5 silver**""",
    '3': """1. **Place 1 congregation on Ephesus** *(During the 3 years Paul spends in Ephesus, he has a fruitful ministry. Those who used to practice magical arts burned their books. The total amount of these was 50,000 silver pieces (Acts 19:18-20))*
2. **Place 7 elders on Jerusalem and get 5 silver** *(Brings money back to Judea for famine relief administration (Acts 20:4))*"""
}
