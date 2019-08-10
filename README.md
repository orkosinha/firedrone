# firedrone
Made for the [FireDrone.AI](https://firedrone.devpost.com/) hackathon.

Our Natural model was trained on Azure Notebooks. We also used the Firenet model found [here](https://github.com/tobybreckon/fire-detection-cnn).
Both models are hosted on Azure Machine Learning Services.

## Strategy
We chose a multimodal approach to detecting fire from the drone field of view image. We believe this was the most effective method due to the shortcomings of the Firenet model discussed more in depth [here](https://breckon.org/toby/publications/papers/dunnings18fire.pdf).
The FireNet model struggled to classify forest fires, street fires (important for the theme of this hackathon), and sunsets, so we chose to use this model along with our custom model.
The Natural network is a much smaller network than FireNet, but it performs better in the specific cases where FireNet struggles. We also generated a custom bitmask to frames where we detected fire using our networks to complete the complex scoring objective of the hackathon.

To balance the two models, we start with analysis using Natural, if a fire is not detected we check Firenet, and then if nothing is detected we use a persistant mask. 
The persistant mask operates on an observation from the drone where we noticed adjacent frames had redundant information, which we may have classified correctly in the frame prior. 
To improve accuracy, we chose to shift our mask by an equivalent drone movement to correctly score newer misclassified frames using prior information.

## Running
To run our `fireDrone.py` program, install the dependencies with 
```
pip install -r requirements.txt
```
and
```
python3 fireDrone.py
```

The program will ask you for the scene ID you want to run. A full list of scene IDs can be found [here](https://github.com/solliancenet/firedrone-hack-starter/blob/master/direct-runs.md).

It will also ask you about which strategy you want to deploy. Generally, based on the name of the scene, we choose to select either the `natural` strategy (for fires that involve more natural areas) or the `multi` strategy for more diverse scenes.

## Utilities
The `./utilities` folder has a few scripts that we used throughout our development process
We used `run_end.py` to end runs that ended unexpectedly and `frameGrab.py` to compile a folder of frames and stiched images to use in our model building. The `run_history.py` generates `last_run.json` to look at the details of our last run. We also used `ws.py` to interact with our drone through the python shell.
