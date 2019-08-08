import firedrone.client as fdc
from firedrone.client.errors import FireDroneClientHttpError
import os

api_key = 'MaH!2iNyY1C3vfyusR%?FmDu@!mZMl9Ns8Syby?9ZPB*rJ&X$b^0fCduWj_$&9m7'

workspace = fdc.Workspace(api_key)

scenes = workspace.get_scenes()

run_id = '8062aad3-7e8a-405e-a343-8025b84b691f'

workspace.directrun_end(run_id)
