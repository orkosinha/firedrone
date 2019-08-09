import json

exec(open('ws.py').read())
last_run = json.loads(json.dumps(workspace.directrun_get_history()))[
    'directRuns']
last_run = last_run[len(last_run) - 1]

last_entry = workspace.directrun_get_history_entry(last_run)

with open('last_run.json', 'w') as outfile:
    json.dump(entry_data, outfile)

"""
public enum DirectRunLogEventType
{
    DirectRunStart = 1,
    DirectRunEnd = 2,

    DroneMoveUp = 3,
    DroneMoveDown = 4,
    DroneMoveLeft = 5,
    DroneMoveRight = 6,

    DroneGetFieldOfViewImage = 7,

    ScoreImage = 8,
    ScoreImagePixels = 9
}
"""
