import hashlib
import re
import sys

import numpy as np


def unescape(str):
    placeholder = "<TMP>"
    assert placeholder not in str
    return str.replace("\\\\n", placeholder).replace("\\n", "\n").replace(placeholder, "\\n").replace("\\\\r", placeholder).replace("\\r", "\r").replace(placeholder, "\\r")


def parse_output(output):
    if len(output) == 0:
        return "FAILED"

    output_hash = hashlib.md5(output.encode("utf-8")).hexdigest()
    if output_hash in {"0267dd217f1113115fb6f3b153283b83", "4478c070ba4ebe9060ccae5ebddeb8f6", "a537ca828e3dff11d10753f74134010f", "55933b16d40dccd1199d0671482ec960", "e26b39f212819f5739d19051c1d3b21e", "9bb23232dc65280f461b1bba330a960a", "a82d3eb490e8ddca43f0bb46edc587b8", "6a87d66ef89bb2f3d17e7779f36a3ff2", "68243259c3ffaba3dbd62fae99a1b689", "b15f475eaaad7bf0e254918750002324", "cc82693381ddaa0979da50b8cee32082", "8fcc76799dad7ba51a1a4cd02c849bed", "c91f6a1d1dc9e91bf15378dc2c207248", "0b4d4df6a744bc4fb0ddb69793b67d60", "1ecb49ec5333156eba065a70a69d5efc", "b2df0d9158be4d82dc3f812c7a403a47", "a31fd50a7c9e1620c8cb511ebdf041dd", "994f97c948375bb89f45346b31cd7bf7", "6ca030b0b24ed40f88e1cf42db5d8b93", "ab300b02620e60602b174d52dd3ec09e", "c2f7e1a264e4eae6d3d034c8ef4432eb", "53d49c7fd2799c5c6449a3020a404361", "14f1378f3f7e1be155317605697fde74", "58282b7d853231ad7a5a37a577f6a8c2", "19c965b140175302beb18fb566c06939", "3583a68a86427ef11f20e164d33fd006", "d8bbe43f7fb1d9b4b6a655dd20aa1d23", "4de5e5445c844335d8098e9847903889", "d45cf6954f87323678c0f47514349c2a", "1fde4babb19a93a0af31f3a9f9a5e645", "f07e20efe5ef914020b1962990ac48f0", "95a46931beb496b8c04c24082d952a00", "8f116a7ba36e392792e8668b2f641d4f", "2d231802949da23ab5f5f9b778ea81f9", "46bd572da6adc4f891b1534078b20e6b", "ab55e2c6bac7d73cd87c0913e7ffe0c6", "b4eafe115130250406f3630cbc5ba5d5", "40c77f9b43e92001ae977ce6cc5dfa98", "3cf6fad2af9ce5c27e2abb9cdb5e63e3", "d8168ea95e291ba079bfb2c9ea4e4e30", "8b26bf8becaee39b7f56660aa4a5a0ec", "0661df39efc8f2a77d2c2dadbbe39d7a", "201e59248822a9c5984bd01403e06177", "5b444ece945fbbd3260fe25ff9232a3e", "d1db0ef79aeba1a714e25e5402d74e28", "33081d317d2547f1175e353f28442792", "76ef7104b97af74b14585fe5ef082618", "d52056254520506638b89e61532cec80", "451ba82c35bb7835caac094d1affd093", "72b0b49b20bc3ba28004a14ce94c0d89", "0038bbd24746105fa154de52006aaae4", "96db9c84993c6e485b5f6a45d88d5fcf", "29ce648edc6f5b33ec4315d192e532b3", "92bd2c3932ee7e01a46213b9218154a0", "e8d1445cf01e0d2dd0ef4857475f9528", "f8e1328d36163e2c3ac36aaf63130c58", "7900721d925513fdaeec12fd88230f2c", "6459d879ca07fbe22545fe29976e96d4", "902f087878add0f9e760e6d3aa56e69c", "9199727fbc9843e6cc7537b29f05d138", "96a692745c21eb162e9482fa06e4192a", "02a6fd1da2506ad1c98e8ed716b68359", "258f2a7388b4d7d8b86dd9501623de0d", "480ae09abb178e622a7582ea2f1d0dde", "fa11b3828ff7901471234343c3861bc0", "61cd671db57d7c75a6dbdfe0939b9541", "0c4c08579d1d4afacc3910428888f2a3", "c1b62fdc1b5bc27377da727bea1b0cd4", "bc7a49bed4f9869672677e7ab885e367", "adf0da2234d7eefd570fc7f1c1b5391a", "781ef72018b55b1d429cb89bcdbd6b8b", "a1de3f70fdbf6624789159ec6ee8b5ea", "4fba0afa1b5e74d007bdff47de5ae996", "244b131beeaa24a42b3bc6c4b899b51d", "dd5d50f44e23f59d0b7a74cad9051f52", "c990c9d4659392a836f52ea224b89fc8", "96b7759758d5df3753bace3d7c017d3a", "2ae1cfd27e6df1028598ac795aee70f7", "16f497b5e37135539f546974b05bcff8", "1d77e3ac72ed59e6406fe1e57ca29916", "255b179c9081fcae153cb8e1e1231aa2", "6c35cc432877a694576e5e9c3ca3228f", "38d1fe38f10aee369185c55867f83849", "e8568dbe24718ce1020f301a61fadf93", "2b9dadbaf8773cfbf079997d4f2e28a9", "f6a5c3ed0f984148b7b48edf16da7814", "f4e168d4a713cccafebb267c0bb0526a", "235d60039a512d03935600899871af7f", "2188b1c96a4d9b5b9ffb4956de6a5d03", "570c9295e6540f479e24740852b46b2d", "09ae9ecc577e2dfd79fcc1790766a667", "16326828425040499900c22e034b949b", "566310b60cb17ab00c844b9b687fe2f6", "bd74dd52f0ae7d397506743792f19405", "c5b35fbb4e8c43f32db40c54780b541f", "44a5bbd958d3f756a77aee0e59e8399f"}:
        # a few cases we manually inspected that can't be parsed
        return "FAILED"

    output = output.replace(",", "").replace("С", "C")

    if (match := re.search("^[0-9A-Z]+$", output)) is not None:
        return output

    output = output.rstrip("\n$ `")
    if output.endswith("\n"):
        output = output[:-1]
    output = output.replace("\\text{", "")

    boxed_regex = r"boxed{(\\text{)?(result=)?([0-9A-Z]+(_{?[0-9]+}?)?\s*\+\s*[0-9A-Z]+(_{?[0-9]+}?)?\s*=\s*)?(0x)?([0-9A-Za-f \\.]+)(_ ?{?(base-)?([0-9]+|ten)}?)?}?(_{?([0-9]+|ten)}?)?}"
    get_result_from_boxed_regex = lambda match: match[-6].replace(" ", "").replace("\\", "")
    # match all \boxed{...} but also make sure there's only one match
    match = re.findall(boxed_regex, output)
    if len(match) >= 1 and all(get_result_from_boxed_regex(m) == get_result_from_boxed_regex(match[0]) for m in match):
        return get_result_from_boxed_regex(match[0])

    last_line = output.split("\n")[-1]
    match = re.findall(boxed_regex, last_line)
    if len(match) >= 1 and all(get_result_from_boxed_regex(m) == get_result_from_boxed_regex(match[0]) for m in match):
        return get_result_from_boxed_regex(match[0])

    last_line = output.rstrip(" .").split(".")[-1]
    match = re.findall(boxed_regex, last_line)
    if len(match) >= 1 and all(get_result_from_boxed_regex(m) == get_result_from_boxed_regex(match[0]) for m in match):
        return get_result_from_boxed_regex(match[0])

    if (match := re.search(r"\\boxed{[0-9A-Z]+}(_{?[0-9]+}?)?\s*\+\s*\\boxed{[0-9A-Z]+}(_{?[0-9]+}?)?\s*=\s*\\boxed{([0-9A-Z]+)}(_{?[0-9]+}?)?\.?$", last_line)) is not None:
        return match.groups()[-2]

    if (match := re.search(r"\\boxed{([0-9A-Z]+)_{?[0-9]+}?\s*=\s*[0-9A-Z]+_{?10}?}\$?\.?$", last_line)) is not None:
        return match.groups()[0]

    if (match := re.search(r"\$?[0-9A-Z]+(_{?[0-9]+}?)\s*\+\s*[0-9A-Z]+(_{?[0-9]+}?)\s*=\s*(0x)?([0-9A-Z]+)(_{?[0-9]+}?)\$?( in base-[0-9]+)?\.?$", output)) is not None:
        return match.groups()[-3]

    if (match := re.search(r"(=|is):?\s*\$?\\boxed{(0x)?([0-9A-Z]+)}\$? \(?in base-[0-9]+\)?,?( and| or| =) \$?\\boxed{(0x)?[0-9A-Z]+}\$? \(?in (base-10|decimal)\)?\.?$", output)) is not None:
        return match.groups()[2]
    if (match := re.search(r"(=|is):?\s*\$?\\boxed{(0x)?[0-9A-Z]+}\$? \(?in (base-10|decimal)\)?,?( and| or| =) \$?\\boxed{(0x)?([0-9A-Z]+)}\$? \(?in base-[0-9]+\)?\.?$", output)) is not None:
        return match.groups()[-1]
    # \boxed{207}_{10}$ which in base-11 is $\boxed{18A}$.
    if (match := re.search(r"\\boxed{[0-9A-Z]+}_\{10\}\$? which in base-[0-9]+ is \$?\\boxed{(0x)?([0-9A-Z]+)}\$?\.?$", output)) is not None:
        return match.groups()[-1]
    # 39 + 31 = 5A\boxed{}
    if (match := re.search(r"[0-9]+\s*\+\s*[0-9]+\s*=\s*([0-9A-Z]+)\\boxed\{\}\.?$", output)) is not None:
        return match.groups()[-1]

    # \boxed{result}\n62
    if (match := re.search(r"\\boxed{result}\s*(\n|=)?\s*([0-9A-Z+*^. ]+=\s*)?([0-9A-Z.]+)\$?\.?\**}?$", output)) is not None:
        return match.groups()[-1]

    # \boxed{result: 62}
    if (match := re.search(r"\\boxed{result: ([0-9A-Z]+)}$", output)) is not None:
        return match.groups()[0]

    match = re.findall(r"[0-9A-Z]+\s*\+\s*[0-9A-Z]+\s*=\s*(0x)?([0-9A-Z]+)", last_line)
    if len(match) == 1:
        return match[0][1]

    match_after_semicolon = r"\s+((\n|[ 0-9A-Z*^])+(\+(\n|[ 0-9A-Z*^])+)+(=|-+|_+)\s*)*([0-9A-Z]+)\s*(\(?(in )?base-[0-9]+\)?)?(, which [^,.]+)?(\s*\([^()]+\))?\.?$"
    if (match := re.search(r"\n([0-9A-Z]+)$", output)) is not None:
        return match.groups()[-1]
    if (match := re.search(r" in base-[0-9]+ is (equal to )?\"?(0x)?([0-9A-Z]+)\"?( base-[0-9]+)?(, (or|since) [^.]+)?( \([^()]+\))?\.$", output)) is not None:
        return match.groups()[-5]
    if (match := re.search(r" in base-[0-9]+: \$?([0-9A-Z]+)\$?\.$", output)) is not None:
        return match.groups()[-1]
    if (match := re.search(r" the base-[0-9]+ sum: ([0-9A-Z]+)\.$", output)) is not None:
        return match.groups()[-1]
    if (match := re.search(r"the result in base-[0-9]+ is ([0-9A-Z]+), which is equal to [0-9 *^+()]+\.$", output)) is not None:
        return match[1]
    if (match := re.search(r"the sum of [0-9A-Z]+ and [0-9A-Z]+ (in base-[0-9]+ )?(is|as):?" + match_after_semicolon, output)) is not None:
        return match.groups()[-5]
    if (match := re.search(r"the result of [0-9A-Z]+\s*\+\s*[0-9A-Z]+ (in base-[0-9]+ )?(is|as):?" + match_after_semicolon, output)) is not None:
        return match.groups()[-5]
    if (match := re.search(r"[0-9A-Z]+\s*\+\s*[0-9A-Z]+( in base-[0-9]+)?,? (which )?(equals|is equal to|as):? \$?([0-9A-Z]+)\$?(, written as [0-9A-Z]+)?\.?$", output)) is not None:
        return match.groups()[-2]
    if (match := re.search(r"in base-10 is \$?[0-9]+\$?,? (which )?(equals|is equal to|as):? \$?([0-9A-Z]+)\$?(, written as [0-9A-Z]+)?\.?$", output)) is not None:
        return match.groups()[-2]
    if (match := re.search(r"[0-9A-Z]+\s*\+\s*[0-9A-Z]+\s*=\s*([0-9A-Z]+)( in base-[0-9]+)?\.?$", output)) is not None:
        return match.groups()[-2]
    if (match := re.search(r"we can simply write the result as ([0-9A-Z]+)\.?$", output)) is not None:
        return match.groups()[-1]
    if (match := re.search(r"which can be written as ([0-9A-Z]+)\.?$", output)) is not None:
        return match.groups()[-1]
    if (match := re.search(r"(which gives|giving) us the( base-[0-9]+)? number ([0-9A-Z]+)\.?$", output)) is not None:
        return match.groups()[-1]
    if (match := re.search(r"the final result is simply the sum of the tens and ones places: ([0-9A-Z]+)\.?$", output)) is not None:
        return match.groups()[-1]
    if (match := re.search(r"the result is simply the combination of these two sums: ([0-9A-Z]+)\.?$", output)) is not None:
        return match.groups()[-1]
    if (match := re.search(r"we have ([0-9A-Z]+) in base-[0-9]+ as the (final answer for|result of|sum of) [0-9A-Z]+ (\+|and) [0-9A-Z]+\.$", output)) is not None:
        return match[1]
    if (match := re.search(r"we (have|get|end up with) ([0-9A-Z]+)( in base-[0-9]+)? as the( final)? (result|answer|sum)( in base-[0-9]+)?\.$", output)) is not None:
        return match.groups()[1]
    if (match := re.search(r"(=| is) \"?([0-9A-Z]+)\"?\s*(\s+\(?(in )?base-[0-9]+\)?)?\.?$", output)) is not None:
        return match.groups()[1]
    if (match := re.search(r"( final)?( base-[0-9]+)? (result|answer|sum)( in base-[0-9]+)?( is)?( simply)?( of)?( as)?:?" + match_after_semicolon, output)) is not None:
        return match.groups()[-5]
    if (match := re.search(r"we get:" + match_after_semicolon, output)) is not None:
        return match.groups()[-5]
    if (match := re.search(r"we can add the two numbers in base-[0-9]+:" + match_after_semicolon, output)) is not None:
        return match.groups()[-5]
    if (match := re.search(r"[tT]he combination of these sums:\s+([0-9A-Z]+)(\(in base-[0-9]+\))?\.?$", output)) is not None:
        return match.groups()[-2]
    if (match := re.search(r"(Result|Answer)( is)?:?\s+([0-9A-Z]+)\.?$", output)) is not None:
        return match.groups()[-1]
    if (match := re.search(r"The decimal equivalent of \$?([0-9A-Z]+)\$? is therefore \$?[0-9A-Z]+\$?\.?$", output)) is not None:
        return match.groups()[0]
    if (match := re.search(r"(T|t)he final (result|answer) is:?\s+([0-9A-Z ]+\s*\+\s*[0-9A-Z ]+\s*(=|-+)+\s*)?([0-9A-Z ]+)(\(in base-[0-9]+\))?\.?\**$", output)) is not None:
        return match.groups()[-2].replace(" ", "")
    if (match := re.search(r" in base-[0-9]+ is (equal to )?\"?(0x)?([0-9A-Z ]+)\"?(, or [^,.]+)?\.$", output)) is not None:
        return match.groups()[-2].replace(" ", "")
    if (match := re.search(r"( |(\n))([0-9A-Z]+) \(?in base-[0-9]+\)?\.$", output)) is not None:
        return match.groups()[-1]

    print("Failed to parse output:", output)
    print(output_hash)
    assert False


def get_label(expr, base):
    lhs, rhs = expr.split("+")
    lhs_base10 = int(lhs, base)
    rhs_base10 = int(rhs, base)
    sum_base10 = lhs_base10 + rhs_base10
    return np.base_repr(sum_base10, base)


def main(output_file, base):
    base = int(base)

    correct = total = 0
    with open(output_file) as f:
        for line in f:
            line = line.strip("\n ")
            try:
                expr, orig_pred = line.split("\t")
            except ValueError:
                expr, shots, orig_pred = line.split("\t")
            orig_pred = unescape(orig_pred)
            pred = parse_output(orig_pred).upper()
            label = get_label(expr, base)
            if label == pred:
                correct += 1
            total += 1
    print(f"Accuracy: {correct} / {total} = {correct / total}")


if __name__ == "__main__":
    try:
        main(*sys.argv[1:])  # pylint: disable=no-value-for-parameter,too-many-function-args
    except Exception as e:
        import pdb
        import traceback

        if not isinstance(e, (pdb.bdb.BdbQuit, KeyboardInterrupt)):
            print("\n" + ">" * 100 + "\n")
            traceback.print_exc()
            print()
            pdb.post_mortem()
