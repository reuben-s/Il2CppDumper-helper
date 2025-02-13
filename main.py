import json
import time
import argparse
import os

function_counter = {}

def generate_function(function):
    offset = hex(function["Address"])
    signature = function["Signature"]

    # Parse the signature
    split = signature.split("(")
    split_2 = split[0].split(" ")
    restype = split_2[0]
    name = split_2[1]
    arguments_str = split[1][:-2]
    arguments = [list(filter(None, argument.split(" ")))
                 for argument in arguments_str.split(",")]

    # Check if function overload exists
    if name in function_counter:
        function_counter[name] += 1
        name += f"_{function_counter[name]}"
    else:
        function_counter[name] = 0

    # Generate function pointer type definition
    function_pointer = f"typedef {restype} (__fastcall *p_{name})("
    for i in range(len(arguments)):
        if len(arguments[i]) > 1:
            arguments[i].pop()
        arguments[i] = " ".join(arguments[i])
    function_pointer += ", ".join(arguments) + ");"

    # Generate function pointer variable declaration
    function_decl = f"p_{name} {name} = (p_{name})(GameAssembly + offsets::{name});"

    return (name, offset, function_pointer, function_decl)

def generate_header_files(path, output_directory):
    print("Creating header files ...")
    il2cppdumper_helper_h = open(output_directory + "\Il2CppDumper_helper.hpp", "w")
    offsets_h = open(output_directory + "\offsets.hpp", "w")

    il2cppdumper_helper_h.write(
        "#include \"il2cpp.h\"\n#include \"offsets.hpp\"\n\nnamespace Il2CppDumper {\n\t// Pointer to GameAssembly.dll base\n\tconst std::ptrdiff_t GameAssembly = reinterpret_cast<std::ptrdiff_t>(GetModuleHandle(TEXT(\"GameAssembly.dll\")));")
    offsets_h.write("#include <cstddef>\n\nnamespace Il2CppDumper {\n\tnamespace offsets {")

    print("Parsing function signatures ...")
    with open(path, "r") as script:
        raw = script.read()
        script_methods = json.loads(raw)["ScriptMethod"]
        for function in script_methods:
            name, offset, function_pointer, function_decl = generate_function(
                function)
            il2cppdumper_helper_h.write(
                f"\n\t// {function['Name']}\n\t{function_pointer}\n\t{function_decl}")
            offsets_h.write(f"\n\t\tconstexpr std::ptrdiff_t {name} = {offset};")

    il2cppdumper_helper_h.write("\n}")
    offsets_h.write("\n\t}\n}")

    il2cppdumper_helper_h.close()
    offsets_h.close()

def main():
    start = time.time()

    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=str, required=False, help="Path to Il2CppDumper script.json file.", default=os.getcwd() + "\script.json")
    parser.add_argument("--output", type=str, required=False, help="Path to the output header files.", default=os.getcwd())
    args = parser.parse_args()

    if not os.path.exists(args.path):
        parser.error("Could not find script.json. Use --path to specify a path to the file.")
    if not os.path.exists(args.output) or os.path.isfile(args.output):
        parser.error("Could not find output directory. Use --output to specify a path to the directory.")

    generate_header_files(args.path, args.output)

    print(f"Generated header files in directory: {args.output}.")
    print(f"Time taken: {round(time.time() - start, 2)} seconds.")

if __name__ == "__main__":
    main()
