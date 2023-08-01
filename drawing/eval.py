import os
import sys

import torch
from eval_utils import NAME2MODEL, encode_classes, encode_one_dir, load_images
from transformers import CLIPModel, CLIPProcessor, CLIPTokenizer

TOPK = (1, 5)
TYPE2TRANSFRROMS = {
    "default": ["r0"],
    "r90": ["r90", "r270"],
    "r180": ["r180"],
    "vflip": ["vflip"],
}


def class_accuracy(output, target, topk=(1,)):
    pred = output.topk(max(topk), dim=-1)[1]
    correct = pred.eq(target[:, None].expand_as(pred)).float()
    class_acc = []
    for k in topk:
        any_k_correct = correct[:, :k].sum(1).clamp(max=1)
        class_acc.append(any_k_correct)
    return class_acc


def main(data_file, output_dir, type, result_file=None, model_name="large"):
    model_name = NAME2MODEL[model_name]
    device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")

    model = CLIPModel.from_pretrained(model_name).to(device)
    processor = CLIPProcessor.from_pretrained(model_name)
    tokenizer = CLIPTokenizer.from_pretrained(model_name)

    labels = [line.strip() for line in open(data_file)]
    text_embeds = encode_classes(labels, tokenizer, model)
    n = len(labels)
    img2txt_class_acc = []
    imgs, num_missing = load_images(labels, output_dir)
    transforms = TYPE2TRANSFRROMS[type]

    for transform in transforms:
        image_embeds = encode_one_dir(imgs, model, processor, transform)
        assert image_embeds.shape[0] == n

        logits_per_image = torch.matmul(image_embeds, text_embeds.t())
        targets = torch.arange(n).long()
        img2txt_class_acc.append(class_accuracy(logits_per_image, targets, topk=TOPK))

    img2txt_acc = []
    for i in range(len(TOPK)):
        best_img2txt_acc = torch.stack(
            [acc[i] for acc in img2txt_class_acc], dim=-1
        ).max(dim=-1)[0]
        img2txt_acc.append(100 * best_img2txt_acc.sum().item() / n)

    print("====================Summary====================")
    print(f"Output dir: {output_dir}")
    print(f"Transformation: {transforms}")
    print(f"Model name: {model_name}")
    print(f"Number of images: {n}")
    print(f"Number of missing images: {num_missing}")
    print(f"Accuracy:", end=" ")
    print(", ".join([f"Top {k}: {acc}" for acc, k in zip(img2txt_acc, TOPK)]))

    if result_file is not None:
        if not os.path.exists(result_file):
            header = "output_dir,num_examples,num_missing,top1,top5\n"
            with open(result_file, "w") as f:
                f.write(header)
        with open(result_file, "a") as f:
            f.write(
                f"{output_dir},{n},{num_missing},{img2txt_acc[0]},{img2txt_acc[1]}\n"
            )


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
