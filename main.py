# gonna use this for mostly printing rn i guess
import json

with open('playerList.json','r') as Plistjson:
    player_list = json.load(Plistjson)

def add_Player(playerName):
    player_list.append(playerName)


while True:
    print('what to do?\n1. add player\n2. list all players\n3. exit')
    action = input()

    if action == '1':
        uuid = input('uuid: ')
        add_Player(uuid)
    if action == '2':
        print(f'\nplayer list: {player_list}')
    if action == '3':
        quit()

