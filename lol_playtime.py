import base64
import http.client
import json
import re
import ssl
import subprocess

def get_time_played(last_season:int=20):
    '''
    Get the total time played in League of Legends

    Args:
        last_season: int, the last season to check for time played
    Returns:
        time_played: int, total time played in seconds
        user_info: tuple, (gameName, tagLine, puuid)
    '''
    time_played = 0
    
    process = subprocess.Popen("wmic PROCESS WHERE name='LeagueClientUx.exe' GET commandline",
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, error = process.communicate()

    # If client not running
    if "No Instance(s) Available." in error.decode('utf-8'):
        return -1
    
    # Get port and token from output
    port = re.search(r'--app-port=([0-9]*)', output.decode('utf-8')).group(1)
    token = re.search(r'--remoting-auth-token=([\w-]*)', output.decode('utf-8')).group(1)
    credentials = base64.b64encode(f'riot:{token}'.encode('utf-8')).decode('utf-8')
        
    # Perform request to get career stats
    conn = http.client.HTTPSConnection("127.0.0.1", port, context=ssl._create_unverified_context())
    headers = {'Authorization': f'Basic {credentials}'}
    conn.request("GET", "/lol-summoner/v1/current-summoner", headers=headers)
    res = conn.getresponse()
    data = json.loads(res.read().decode("utf-8"))

    user_info = {"game_name":data["gameName"], "tag_line":data["tagLine"], "puuid":data["puuid"]}

    # Loop over seasons
    for i in range(8, last_season + 1):
        conn.request("GET", f"/lol-career-stats/v1/summoner-games/puuid/season/{i}",
                     headers=headers)
        res = conn.getresponse()
        data = json.loads(res.read().decode("utf-8"))

        for game in data:
            time_played += game["stats"]["CareerStats.js"]["timePlayed"]

    # Convert time to seconds and add to user_info
    user_info["time_played"] = time_played/1000
    return user_info

if __name__ == "__main__":
    user_info = get_time_played()

    if user_info == -1:
        print("League of Legends is not running.")
    else:
        print(f"{user_info['game_name']}#{user_info['tag_line']} has played {user_info['time_played']/3600} hours.")
