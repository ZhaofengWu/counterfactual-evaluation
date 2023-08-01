import os
import re
import sys

DEFAULT_SETUP = """void setup() {
    size(400, 400);
    background(255);
}"""
SETUP = "void setup()"
DRAW = "void draw()"
GLOBAL = "global"


def add_save_frame(draw_fn, obj):
    index = draw_fn.rindex("}")
    return (
        draw_fn[:index] + f'\n  saveFrame("{obj}.png");\n  exit();\n' + draw_fn[index:]
    )


def add_background_and_size(draw_fn):
    add_code = ""
    if "background" not in draw_fn:
        add_code = f"\n  background(255);\n"
    if "size" not in draw_fn:
        add_code += f"\n  size(400, 400);\n"
    index = draw_fn.index("{") + 1
    return draw_fn[:index] + add_code + draw_fn[index:]


def parse_global_vars(code):
    global_vars = []
    stack = []
    open_paren = 0
    for char in code:
        stack.append(char)
        if char == "{":
            open_paren += 1
        elif char == "}":
            open_paren -= 1
        if char == ";" and open_paren == 0:
            lines = "".join(stack).split("\n")
            for i in range(len(lines) - 1, -1, -1):
                line = lines[i]
                if line.startswith("int") or line.startswith("float"):
                    global_vars.append("\n".join(lines[i:]))
            stack = []
    return global_vars


def parse_functions(code):
    stack = []
    functions = {}
    current_function = None
    current_code = ""
    capture_function_name = False

    for char in code:
        if char.isalpha() and current_function is None:
            capture_function_name = True
            current_code += char
        elif capture_function_name:
            if char == "{":
                current_function = current_code.split("{")[0].strip().split("\n")[-1]
                capture_function_name = False
            else:
                current_code += char
        if char == "{":
            stack.append("{")
            current_code += char
        elif char == "}":
            stack.pop()
            current_code += char
            if len(stack) == 0:
                is_fn = ("=" not in current_function) and (
                    not current_function.startswith("for")
                )
                if is_fn:
                    idx = current_code.index(current_function)
                    functions[current_function] = current_code[idx:]
                current_function = None
                current_code = ""
        else:
            if current_function is not None:
                current_code += char
    return functions


def parse_output(output, obj):
    output = output.replace("\\n", "\n")
    languages = ["processing", "java", ""]
    for language in languages:
        all_functions = {}
        all_global_vars = []
        pattern = r"```{}\s*([\s\S]+?)\s*```".format(language)
        matches = re.findall(pattern, output)
        if matches:
            for match in matches:
                global_vars = parse_global_vars(match)
                for var in global_vars:
                    if var not in all_global_vars:
                        all_global_vars.append(var)
            for match in matches:
                match = match.replace("\\n", "\n")
                try:
                    functions = parse_functions(match)
                    for fn_name, fn in reversed(functions.items()):
                        all_functions[fn_name] = fn
                except:
                    continue
            if DRAW in all_functions:
                all_functions[DRAW] = add_save_frame(all_functions[DRAW], obj)
                if SETUP not in all_functions:
                    all_functions[SETUP] = DEFAULT_SETUP
            elif SETUP in all_functions:
                all_functions[SETUP] = add_save_frame(all_functions[SETUP], obj)
            else:
                all_functions = {}
                sketch_string = "\n  " + "\n".join(matches).replace("\n", "\n  ")
                all_functions[SETUP] = (
                    "void setup() {\n  background(255);\n" + sketch_string + "\n}"
                )
                all_functions[SETUP] = add_save_frame(all_functions[SETUP], obj)
            all_functions[SETUP] = add_background_and_size(all_functions[SETUP])
            global_vars_str = "\n".join(all_global_vars) + "\n\n"
            return global_vars_str + "\n\n".join([fn for fn in all_functions.values()])
    print(f"No matches found for {obj}!")


def main(data_file, output_file, save_dir):
    os.makedirs(save_dir, exist_ok=True)
    data = [line.strip().replace(" ", "_") for line in open(data_file)]
    with open(output_file) as f:
        for obj, line in zip(data, f):
            fields = line.strip().split("\t")
            if len(fields) <= 3:
                continue
            response = fields[1]
            sketch_string = parse_output(response, obj)
            if not sketch_string:
                continue
            obj_dir = os.path.join(save_dir, obj)
            os.makedirs(obj_dir, exist_ok=True)
            obj_path = os.path.join(obj_dir, f"{obj}.pde")
            if os.path.exists(obj_path):
                print(f"Object {obj} already exists!")
                continue
            with open(obj_path, "w") as f:
                f.write(sketch_string)
    print(f"Saved number of objects: {len(os.listdir(save_dir))}")


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
