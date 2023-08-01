import os

import torch
from PIL import Image

TEMPLATES = [
    "a sketch of {}",
    "a drawing of {}",
    "an image of {}",
    "a picture of {}",
    "a doodle of {}",
]

IMG_SIZE = (400, 400)
ROTATIONS = [0, 90, 180, 270]
NAME2MODEL = {
    "base": "openai/clip-vit-base-patch32",
    "large": "openai/clip-vit-large-patch14",
}


def get_captions(obj):
    if obj[0].lower() in "aeiou":
        obj = "an " + obj
    else:
        obj = "a " + obj
    return [template.format(obj) for template in TEMPLATES]


# Reference: https://github.com/openai/CLIP/blob/main/notebooks/Prompt_Engineering_for_ImageNet.ipynb
def encode_classes(classes, tokenizer, model):
    with torch.no_grad():
        class_embeds = []
        for class_name in classes:
            captions = get_captions(class_name)
            inputs = tokenizer(captions, return_tensors="pt", padding=True).to(
                model.device
            )
            text_embeds = model.get_text_features(**inputs)
            text_embeds = text_embeds / text_embeds.norm(dim=-1, keepdim=True)
            class_embed = text_embeds.mean(dim=0)
            class_embed = class_embed / class_embed.norm(dim=-1, keepdim=True)
            class_embeds.append(class_embed)
        class_embeds = torch.stack(class_embeds, dim=0)
    return class_embeds.cpu()


def encode_images(images, processor, model):
    with torch.no_grad():
        inputs = processor(images=images, return_tensors="pt").to(model.device)
        image_embeds = model.get_image_features(**inputs)
        image_embeds = image_embeds / image_embeds.norm(dim=-1, keepdim=True)
    return image_embeds.cpu()


def load_images(labels, output_dir):
    imgs = []
    num_missing = 0
    for label in labels:
        obj = label.replace(" ", "_")
        img_path = os.path.join(output_dir, obj, f"{obj}.png")
        if not os.path.exists(img_path):
            img = Image.new("RGB", IMG_SIZE, color="white")
            num_missing += 1
        else:
            img = Image.open(img_path)
        imgs.append(img)
    return imgs, num_missing


def encode_one_dir(imgs, model, processor, transform):
    if transform.startswith("r"):
        degree = int(transform[1:])
        imgs = [img.rotate(degree) for img in imgs]
    elif transform == "vflip":
        imgs = [img.transpose(Image.FLIP_TOP_BOTTOM) for img in imgs]
    else:
        raise ValueError(f"Unknown transform: {transform}")
    image_embeds = encode_images(imgs, processor, model)
    return image_embeds
