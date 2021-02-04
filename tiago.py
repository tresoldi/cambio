import csv

import alteruphono
import maniphono


def main():
    # Read resources and try to parse them all
    with open("resources/sound_changes2.tsv", encoding="utf-8") as tsvfile:
        for row in csv.DictReader(tsvfile, delimiter="\t"):
            #if int(row["ID"]) < 646:
            #    continue

            # skip negations
            if "!" in row["RULE"]:
                continue

            print()
            print(row)
            ante = maniphono.parse_sequence(row["TEST_ANTE"], boundaries=True)
            post = maniphono.parse_sequence(row["TEST_POST"], boundaries=True)
            rule = alteruphono.Rule(row["RULE"])

            fw = alteruphono.forward(ante, rule)
            fw_str = " ".join([str(v) for v in fw])

            fw_match = fw_str == str(post)

            bw = alteruphono.backward(post, rule)
            bw_strs = [" ".join([str(v) for v in bw_str]) for bw_str in bw]
            bw_rules = [
                alteruphono.parse_seq_as_rule(str(maniphono.Sequence(cand)))
                for cand in bw
            ]
            bw_match = any(
                [
                    all(alteruphono.check_match(list(ante), bw_rule))
                    for bw_rule in bw_rules
                ]
            )

            print("FW", fw_match, "|", fw_str, "|")
            print("BW", bw_match, "|", bw_strs, "|")

            if not all([fw_match, bw_match]):
            #if True:
                input()


if __name__ == "__main__":
    main()
