import cv2
import firedrone.client as fdc
import json
import numpy as np
import requests


def create_bitmask(frame):
    image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    # Condition 1: R > G > B
    cond1a = (image[:, :, 0] > image[:, :, 1])  # r > g
    cond1b = (image[:, :, 1] > image[:, :, 2])  # g > b
    cond1c = (image[:, :, 0] > image[:, :, 2])  # r > b
    cond1t = np.bitwise_and(cond1a, cond1b)
    cond1 = np.bitwise_and(cond1t, cond1c)
    # Condition 2: Y > Cr > Cb
    YCCimg = cv2.cvtColor(image, cv2.COLOR_RGB2YCR_CB)
    cond2a = (YCCimg[:, :, 0] > YCCimg[:, :, 1])  # y > cr
    cond2b = (YCCimg[:, :, 1] > YCCimg[:, :, 2])  # cr > cb
    cond2c = (YCCimg[:, :, 0] > YCCimg[:, :, 2])  # y > cb
    cond2t = np.bitwise_and(cond2a, cond2b)
    cond2 = np.bitwise_and(cond2t, cond2c)
    # Condition 3: Y > mean(Y) and Cr > mean(Cr) and Cb < mean(Cb)
    meanY = np.average(YCCimg[:, :, 0])
    meanCr = np.average(YCCimg[:, :, 1])
    meanCb = np.average(YCCimg[:, :, 2])
    cond3a = (YCCimg[:, :, 0] > meanY)
    cond3b = (YCCimg[:, :, 1] > meanCr)
    cond3c = (YCCimg[:, :, 2] < meanCb)
    cond3t = np.bitwise_and(cond3a, cond3b)
    cond3 = np.bitwise_and(cond3t, cond3c)
    # Condition 4: Setting min and max thresholds for HSV
    hsv_img = cv2.cvtColor(image, cv2.COLOR_RGB2HSV).astype(np.uint8)
    lower_1 = np.array([4, 100, 220])
    upper_1 = np.array([25, 260, 260])
    hsv1 = cv2.inRange(hsv_img, lower_1, upper_1)
    lower_2 = np.array([50, 100, 220])
    upper_2 = np.array([70, 260, 260])
    hsv2 = cv2.inRange(hsv_img, lower_2, upper_2)
    hsv_mask = cv2.bitwise_or(hsv1, hsv2)
    # Combining the Conditions
    comb = np.bitwise_and(cond1, cond3)
    image[comb == 0] = [0, 0, 0]
    flame = cv2.bitwise_and(image, image, mask=hsv_mask)
    grey = cv2.cvtColor(flame, cv2.cv2.COLOR_BGR2GRAY)
    BW_flame = cv2.threshold(grey, 10, 255, cv2.THRESH_BINARY)[1]
    return BW_flame


def score(move_dir, bitmask):
    frame = workspace.get_drone_fov_image(run_id)
    with open('frame.png', 'wb') as f:
        f.write(frame)
    frame = cv2.imread('./frame.png')

    if strategy == "natural":
        headers = {'Content-Type': 'application/json'}
        natural_uri = 'http://fc91f275-eaa2-464e-8bff-11b3108b8baa.eastus.azurecontainer.io/score'
        NATURAL_DIMS = 64

        natural_frame = cv2.resize(frame, dsize=(NATURAL_DIMS, NATURAL_DIMS),
                                   interpolation=cv2.INTER_AREA)

        test_data = json.dumps({'image': natural_frame.tolist()})
        response = requests.post(natural_uri, data=test_data, headers=headers)
        if (response.json()['fire'] > 85):
            bitmask = create_bitmask(frame)
            # Score Bitmask
            workspace.directrun_score_pixels(
                run_id, bitmask.flatten().astype(int).tolist())
            print("Score from natural")

        return bitmask

    elif strategy == "multi":
        # Phase 1: Use our natural network for fire presence
        headers = {'Content-Type': 'application/json'}
        natural_uri = 'http://fc91f275-eaa2-464e-8bff-11b3108b8baa.eastus.azurecontainer.io/score'
        NATURAL_DIMS = 64

        natural_frame = cv2.resize(frame, dsize=(NATURAL_DIMS, NATURAL_DIMS),
                                   interpolation=cv2.INTER_AREA)

        test_data = json.dumps({'image': natural_frame.tolist()})
        response = requests.post(natural_uri, data=test_data, headers=headers)
        if (response.json()['fire'] > 85):
            bitmask = create_bitmask(frame)
            # Score Bitmask
            workspace.directrun_score_pixels(
                run_id, bitmask.flatten().astype(int).tolist())
            print("Score from natural")

            return bitmask

        else:
            # Phase 2: Use firenet for fire presence
            firenet_uri = 'http://26f07c9d-89dc-4a62-bcbc-1f6a8517df53.eastus.azurecontainer.io/score'
            FIRENET_DIMS = 224
            firenet_frame = cv2.resize(frame, dsize=(FIRENET_DIMS, FIRENET_DIMS),
                                       interpolation=cv2.INTER_AREA)
            test_data = json.dumps({'image': firenet_frame.tolist()})
            response = requests.post(
                firenet_uri, data=test_data, headers=headers)
            if (response.json()['fire'] > 0.85):
                bitmask = create_bitmask(frame)
                # Score bitmask
                workspace.directrun_score_pixels(
                    run_id, bitmask.flatten().astype(int).tolist())
                print("Score from firenet")

                return bitmask

            else:
                if (move_dir == "right"):
                    print("Shifting persistant mask right")
                    bitmask = np.roll(bitmask, -100)
                    bitmask[:, -100] = 0
                elif (move_dir == "left"):
                    print("Shifting persistant mask left")
                    bitmask = np.roll(bitmask, 100)
                    bitmask[:, 99] = 0
                elif (move_dir == "up"):
                    bitmask = np.zeros((500, 500))

                # Check if bitmask contains any 1, if so score, if not don't score
                if any(1 in x for x in bitmask):
                    workspace.directrun_score_pixels(
                        run_id, bitmask.flatten().astype(int).tolist())
                    print("Score from persistant mask")

                return bitmask


def start_run(scene):
    global run_id

    print("Starting run at "+str(scene['name']))

    try:
        start_result = workspace.directrun_start(scene['id'])
        run_id = start_result['uniqueId']
        print("RUN ID: " + run_id)
    except FireDroneClientHttpError as e:
        print(e)

    # Reset to left corner of the scene
    move_result = workspace.directrun_move_left(run_id)
    while move_result['success']:
        move_result = workspace.directrun_move_left(run_id)

    bitmask = np.zeros((500, 500))

    while True:
        # score
        bitmask = score("up", bitmask)
        move_result = workspace.directrun_move_right(run_id)

        # score
        bitmask = score("right", bitmask)
        while move_result['success']:
            move_result = workspace.directrun_move_right(run_id)
            # score
            bitmask = score("right", bitmask)

        move_result = workspace.directrun_move_up(run_id)
        # score
        if not move_result['success']:
            break
        else:
            bitmask = score("up", bitmask)

        move_result = workspace.directrun_move_left(run_id)
        # score
        bitmask = score("left", bitmask)
        while move_result['success']:
            move_result = workspace.directrun_move_left(run_id)
            # score
            bitmask = score("left", bitmask)

        move_result = workspace.directrun_move_up(run_id)
        # score
        if not move_result['success']:
            break

    workspace.directrun_end(run_id)


def main():
    global workspace
    global strategy

    print("Enter the id of the scene you would like to test")
    strategies = ["multi", "natural"]
    scene_id = input("id? ")
    strategy = input("strategy? ")
    while not strategy in strategies:
        print("Invalid strategy\n")
        strategy = input("strategy? ")

    api_key = 'MaH!2iNyY1C3vfyusR%?FmDu@!mZMl9Ns8Syby?9ZPB*rJ&X$b^0fCduWj_$&9m7'

    workspace = fdc.Workspace(api_key)

    scenes = workspace.get_scenes()

    # Check if scene id is a valid scene
    for scene in scenes:
        if (scene['id'] == int(scene_id)):
            start_run(scene)


if __name__ == '__main__':
    main()
