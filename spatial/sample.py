import random
import sys
from collections import defaultdict

from tqdm import tqdm

random.seed(0)

ROOM2OBJETS = {
    "bedroom": [
        "bed",
        "wardrobe",
        "drawer",
        "desk",
        "chair",
        "bookcase",
        "TV",
        "computer",
        "lamp",
        "mirror",
    ],
    "bathroom": ["sink", "toilet", "shower", "bathtub", "mirror"],
    "kitchen": [
        "sink",
        "fridge",
        "microwave",
        "dishwasher",
        "coffee machine",
        "kettle",
        "toaster",
        "blender",
        "table",
        "chair",
    ],
    "living room": ["sofa", "coffee table", "TV", "bookcase", "lamp", "mirror"],
    "dining room": ["table", "chair", "sideboard", "lamp", "mirror"],
    "study room": ["desk", "chair", "computer", "lamp", "bookcase", "mirror"],
    "laundry room": ["washing machine", "dryer", "sink"],
}

DIRECTIONS = ["north", "south", "east", "west"]


def sample_room(num_objects=3, min_dir=3):
    room = random.choice(list(ROOM2OBJETS.keys()))
    objects = random.sample(ROOM2OBJETS[room], num_objects)
    directions = random.sample(DIRECTIONS, min(min_dir, num_objects))
    if len(directions) < num_objects:
        directions += random.choices(DIRECTIONS, k=num_objects - len(directions))
    dir2obj = defaultdict(list)
    for direction, obj in zip(directions, objects):
        dir2obj[direction].append(obj)

    docstring = f"You are in the middle of a {room}. "
    for direction, objects in dir2obj.items():
        objects = [f"a {obj}" for obj in objects]
        header = "There is"
        if len(objects) == 1:
            obj_str = f"{objects[0]}"
        else:
            obj_str = ", ".join(objects[:-1]) + " and " + objects[-1]
        docstring += f"{header} {obj_str} on the {direction} side. "
    return docstring


def main(output_file, n_samples, n_objects):
    n_samples = int(n_samples)
    n_objects = int(n_objects)

    with open(output_file, "w") as f:
        for _ in tqdm(range(n_samples)):
            f.write(sample_room(n_objects) + "\n")


if __name__ == "__main__":
    try:
        main(
            *sys.argv[1:]
        )  # pylint: disable=no-value-for-parameter,too-many-function-args
    except Exception as e:
        import pdb
        import traceback

        if not isinstance(e, (pdb.bdb.BdbQuit, KeyboardInterrupt)):
            print("\n" + ">" * 100 + "\n")
            traceback.print_exc()
            print()
            pdb.post_mortem()
