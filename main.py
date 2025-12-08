from sys import argv as args
import os
import json
import requests
from urllib.request import urlretrieve as download_url
from zipfile import ZipFile

temp_userdata = dict()
if not os.path.exists("SWAv2-CLI_userdata.json"):
    with open("SWAv2-CLI_userdata.json", "x") as f:
        f.write("")


def get_pid_by_name(process_name):
    import psutil
    pids = []
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] == process_name:
            pids.append(proc.info['pid'])
    return pids

def yn_question(prompt):
    question = input(prompt)
    while question.lower() != "y" and question.lower() != "n":
        question = input(prompt)
    return question

def download_to_temp(url, filename, headers = dict()):
    if not os.path.exists(".\\temp\\"):
        os.mkdir("temp")
    fr = requests.get(url, headers=headers)
    with open("temp\\"+filename, "wb") as f:
        f.write(fr.content)
    del fr

def del_temp():
    from shutil import rmtree as rmd
    rmd(".\\temp")
    del rmd
    
def save_ud_config():
    with open("SWAv2-CLI_userdata.json", "w") as f:
        f.write(json.dumps(temp_userdata))

def load_ud_config():
    global temp_userdata
    with open("SWAv2-CLI_userdata.json", "r") as f:
        temp_userdata = json.loads(f.read())

def try_add_game(gameId):
    if temp_userdata.get('user', False):
        user = temp_userdata['user']
    if temp_userdata["code"] == "SWA2-":
        cag = yn_question("Continue as guest? (Y/N) ")
        # curl -X POST https://swacloud.com/api/launcher/connect -d "{\"code\":\"SWA2-CODE-MINE\"}" -H "Content-Type: application/json"
        if cag.lower() == "n":
            code = "SWA2-" + input("Enter SWAv2 authorization code: SWA2-")
            temp_userdata['code'] = code
            userr = requests.request("POST", "https://swacloud.com/api/launcher/connect", json={"code":code})
            user = json.loads(userr.text)
            stc = yn_question("Save the current user to the config file? (Y/N)")
            if stc.lower() == "y":
                temp_userdata["user"] = user
                save_ud_config()
        else:
            user = {"is_guest": True}
    print("Checking game existence...")
    game_fetch = requests.get("https://api.swa-recloud.fun/api/v3/fetch/"+gameId)
    #Game FeTch Result
    gftr = json.loads(game_fetch.text)
    if gftr["File"] == "0":
        print(f"Game with ID {gameId} was not found.")
    else:
        print(f"Game found! ({gftr['name']})")
        print("Preparing to download...")
        print(user)
        if user["is_guest"]:
            if gftr['access'] == "2":
                print("This game is premium access only.")
                return
            print("Downloading...")
            download_to_temp(f"https://api.swa-recloud.fun/api/v3/file/{gameId}.zip", gameId+".zip")
        else:
            print("Downloading...")
            download_to_temp(f"https://api.swa-recloud.fun/api/v3/file/{gameId}.zip", gameId+".zip",
                             headers = {
                                 "X-Username":    user["username"],
                                 "X-Hardware-ID": user["unique_id"],
                                 "X-Unique-ID":   user["unique_id"]
                                 })
        print(f"{gftr['name']} downloaded!")
        print("Extracting files...")
        stp = temp_userdata['steam-path']
        lua_extr_path = stp+'config\\stplug-in'
        manif_extr_path = stp+'config\\depotcache'
        with ZipFile(f"temp\\{gameId}.zip", 'r') as zObject:
            if not os.path.exists(f"temp\\{gameId}"):
                os.mkdir(f"temp\\{gameId}")
            zObject.extractall(path=f"temp\\{gameId}")
        print(f"Extracted files to temp")
        print("Copying files...")
        from shutil import copy2 as cp
        for file in os.listdir(f"temp\\{gameId}"):
            if file.endswith(".lua"):
                cp(f"temp\\{gameId}\\"+file, stp+"config\\stplug-in")
            elif file.endswith(".manifest"):
                cp(f"temp\\{gameId}\\"+file, stp+"config\\depotcache")
        del cp
        print("Files copied!")
        print("Game successfully added!")
        

def main():
    try:
        if args[1] == "setup":
            stp = input("Absolute path to your Steam installation (default: \"C:\\Program Files (x86)\\Steam\\\"): ")
            stp = stp or "C:\\Program Files (x86)\\Steam\\"
            if not stp.endswith("\\"):
                stp += "\\"
            swa_code = input("SWA2 code (leave blank for guest or to enter when logging in): SWA2-")
            if not os.path.exists(stp + "config\\stplug-in"):
                print("Steamtools not found!")
                sttr = yn_question("Would you like to install SteamTools now? (Y/N)").lower()
                if sttr == "y":
                    print("Downloading SteamTools...")
                    download_to_temp("https://drive.usercontent.google.com/u/0/uc?id=161uR_utWzwveGOGM1IZoLyQ_egEpRkOV&export=download", "stplug-in.zip")
                    print("Download done!")
                    extr_path = stp+'config\\stplug-in'
                    os.mkdir(extr_path)
                    with ZipFile("temp\\stplug-in.zip", 'r') as zObject:
                        zObject.extractall(path=extr_path)
                    print(f"Extracted files to {extr_path}")
                    print("Deleting \"temp\" directory...")
                    del_temp()
            temp_userdata['steam-path'] = stp
            temp_userdata['code'] = ('SWA2-' if not swa_code.startswith('SWA2-') else '')+swa_code
            if swa_code != "":
                userr = requests.post("https://swacloud.com/api/launcher/connect", json={"code":('SWA2-' if not swa_code.startswith('SWA2-') else '')+swa_code})
                user = json.loads(userr.text)
                if user['success']:
                    temp_userdata["user"] = user
                else:
                    print("Something went wrong! Your SWA2 code might have been entered incorrectly.")
            save_ud_config()
            print("Setup done!")
        elif args[1] == "add":
            if args[2] == "game":
                if len(args) == 4:
                    load_ud_config()
                    try_add_game(args[3])
                else:
                    print("Supply a Steam game ID to download")
        elif args[1] == "help" or args[1] == "-h" or args[1] == "--help":
            print("""Avaliable commands:
  swa-cli setup - Set up the environment (Steam path, SWAv2 code)
  swa-cli add game [gameid] - Add a game with id [gameid] to Steam
""")
    except IndexError:
        print("""Avaliable commands:
  swa-cli setup - Set up the environment (Steam path, SWAv2 code)
  swa-cli add game [gameid] - Add a game with id [gameid] to Steam
""")
                    
if __name__ == "__main__":
    main()