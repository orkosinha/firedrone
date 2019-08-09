import firedrone.client as fdc
import os
from firedrone.client.errors import FireDroneClientHttpError
from PIL import Image

api_key = 'MaH!2iNyY1C3vfyusR%?FmDu@!mZMl9Ns8Syby?9ZPB*rJ&X$b^0fCduWj_$&9m7'

workspace = fdc.Workspace(api_key)

scenes = workspace.get_scenes()

for scene in scenes:
    try:
        start_result = workspace.directrun_start(scene['id'])
        print("GOING ON RUN: " + start_result['uniqueId'])
        run_id = start_result['uniqueId']
    except FireDroneClientHttpError as e:
        print(e)
        break

    # reset drone to top left
    move_result = workspace.directrun_move_up(run_id)
    while move_result['success']:
        move_result = workspace.directrun_move_up(run_id)
    move_result = workspace.directrun_move_left(run_id)
    while move_result['success']:
        move_result = workspace.directrun_move_left(run_id)

    def capture():
        frame = workspace.get_drone_fov_image(run_id)
        file_name = './frames/frame' + \
            str(scene['id'])+''+"{:02d}".format(x) + \
            '' + "{:02d}".format(y)+'.png'
        with open(file_name, 'wb') as f:
            f.write(frame)
        return file_name

    def horizontal_stich(image_names, file_name):
        images = list(map(Image.open, image_names))

        total_width = 500 + (len(images) - 1)*100

        new_im = Image.new('RGB', (total_width, 500))

        x_offset = 0
        for im in images:
            new_im.paste(im, (x_offset, 0))
            x_offset += 100

        new_im.save(file_name)
        return file_name

    def vertical_stich(image_names, file_name):
        images = list(map(Image.open, image_names))

        total_width = images[0].size[0]
        total_height = 500 + (len(images) - 1)*100

        new_im = Image.new('RGB', (total_width, total_height))

        y_offset = 0
        for im in images:
            new_im.paste(im, (0, y_offset))
            y_offset += 100

        new_im.save(file_name)

    y = 0
    horizontal = []
    vertical = []
    while True:
        x = 0

        horizontal.append(capture())

        move_result = workspace.directrun_move_right(run_id)
        x += 1
        horizontal.append(capture())
        while move_result['success']:
            move_result = workspace.directrun_move_right(run_id)
            if move_result['success']:
                x += 1
                horizontal.append(capture())

        file_name = str(scene['id'])+'horizontal'+str(y)+'.png'
        vertical.append(horizontal_stich(horizontal, file_name))
        horizontal = []

        move_result = workspace.directrun_move_down(run_id)
        y += 1
        if not move_result['success']:
            vertical_stich(vertical, str(scene['id'])+".png")
            break
        else:
            horizontal.append(capture())

        move_result = workspace.directrun_move_left(run_id)
        x -= 1
        horizontal.append(capture())
        while move_result['success']:
            move_result = workspace.directrun_move_left(run_id)
            if move_result['success']:
                x -= 1
                horizontal.append(capture())

        horizontal.reverse()
        file_name = str(scene['id'])+'horizontal'+str(y)+'.png'
        vertical.append(horizontal_stich(horizontal, file_name))
        horizontal = []

        move_result = workspace.directrun_move_down(run_id)
        y += 1
        if not move_result['success']:
            vertical_stich(vertical, str(scene['id'])+".png")
            break

    workspace.directrun_end(run_id)

    print("\n Frames should be in the ./frames directory")
