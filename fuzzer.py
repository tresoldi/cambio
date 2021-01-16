from collections import Counter
import csv
import itertools
from pathlib import Path
import random
import signal

import alteruphono

# List of number of times to perform a given random permutation -- in
# a more serious system this would be something like the result of a
# Poisson process, but here we just hard-code the probabilities
DISTRIBUTION = [0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 3, 3, 4]

OUTPUT_FILE = "fuzzer.log"

# Handler for keyboard signals (for CTRL+C and CTRL+D)
class SIG_handler:
    def __init__(self):
        self.signal = False

    def signal_handler(self, signal, frame):
        print("SIGINT or SIGTERM received, ending execution.")
        self.signal = True


def perturbate_element(elem, chars=None, distribution=DISTRIBUTION):
    # Compute `chars` if not provided
    if not chars:
        chars = Counter(elem)

    # Insert random characters (use weighted char frequency)
    for _ in range(random.choice(distribution)):
        i = random.randrange(sum(chars.values()))
        char = next(itertools.islice(chars.elements(), i, None))
        idx = random.randint(0, len(elem) - 1)
        elem = elem[:idx] + char + elem[idx:]

    # Swap characters; the number of times we
    for _ in range(random.choice(distribution)):
        # get two random indexes; not checking if they are the same
        idx_a = random.randint(0, len(elem) - 1)
        idx_b = random.randint(0, len(elem) - 1)

        elem = list(elem)
        elem[idx_a], elem[idx_b] = elem[idx_b], elem[idx_a]
        elem = "".join(elem)

    # Delete random characters
    elem = "".join(
        [
            char
            for char, rnd in zip(elem, [random.random() for x in range(len(elem))])
            if random.choice(distribution) < distribution[-1]
        ]
    )

    # Replace with random characters, selected uniformly (and not testing if
    # the replace character happens to be the same)
    for _ in range(random.choice(distribution)):
        i = random.randrange(sum(chars.values()))
        char = next(itertools.islice(chars.elements(), i, None))
        idx = random.randint(0, len(elem) - 1)
        elem = elem[:idx] + char + elem[idx + 1 :]

    return elem


def main():
    # Catches SIGINT and SIGTERM
    signal_handler = SIG_handler()
    signal.signal(signal.SIGINT, signal_handler.signal_handler)
    signal.signal(signal.SIGTERM, signal_handler.signal_handler)

    # Read seed data, collecting rules and
    file_path = Path(__file__).parent / "resources" / "sound_changes.tsv"
    with open(file_path.as_posix()) as csvfile:
        rules = []
        seqs = []
        for row in csv.DictReader(csvfile, delimiter="\t"):
            rules.append(alteruphono.utils.clear_text(row["RULE"]))
            seqs.append(alteruphono.Sequence(row["TEST_ANTE"]))
            seqs.append(alteruphono.Sequence(row["TEST_POST"]))

    # Count characters in all rules and seqs
    rule_chars = Counter([char for rule in rules for char in rule])
    seq_chars = Counter([char for seq in seqs for char in seq])

    # Open logging file and write headers
    logger = open(OUTPUT_FILE, "w")
    writer = csv.DictWriter(
        logger,
        delimiter="\t",
        fieldnames=[
            "SUCCESS",
            "ORIGINAL_RULE",
            "FUZZ_RULE",
            "ORIGINAL_SEQ",
            "FUZZ_SEQ",
            "PARSE_EXCEPTION",
            "FORWARD_PLAIN_EXCEPTION",
            "BACKWARD_PLAIN_EXCEPTION",
            "FORWARD_FUZZ_EXCEPTION",
            "BACKWARD_FUZZ_EXCEPTION",
        ],
    )
    writer.writeheader()

    # Main loop
    counter = 0
    errors = 0
    while True:
        counter += 1
        if counter % 10 == 0:
            print(f"Iteration #{counter}, {errors} error so far...")

        # Holder for this test data
        test = {
            "SUCCESS": True,
            "PARSE_EXCEPTION": "",
            "FORWARD_PLAIN_EXCEPTION": "",
            "BACKWARD_PLAIN_EXCEPTION": "",
            "FORWARD_FUZZ_EXCEPTION": "",
            "BACKWARD_FUZZ_EXCEPTION": "",
        }

        # Get a random starting rule, making a copy for reference
        test["ORIGINAL_RULE"] = random.choice(rules)
        test["FUZZ_RULE"] = perturbate_element(test["ORIGINAL_RULE"], rule_chars)

        # Parse
        try:
            rule_obj = alteruphono.Rule(test["FUZZ_RULE"])
        except Exception as e:
            if not isinstance(e, alteruphono.utils.AlteruPhonoError):
                test["SUCCESS"] = False

            rule_obj = None
            test["PARSE_EXCEPTION"] = str(e)

        # Attempt to apply to a "real" sequence
        test["ORIGINAL_SEQ"] = str(random.choice(seqs))
        try:
            alteruphono.forward(alteruphono.Sequence(test["ORIGINAL_SEQ"]), rule_obj)
        except Exception as e:
            if not isinstance(e, alteruphono.utils.AlteruPhonoError):
                test["SUCCESS"] = False
            test["FORWARD_PLAIN_EXCEPTION"] = str(e)
        try:
            alteruphono.backward(alteruphono.Sequence(test["ORIGINAL_SEQ"]), rule_obj)
        except Exception as e:
            if not isinstance(e, alteruphono.utils.AlteruPhonoError):
                test["SUCCESS"] = False
            test["BACKWARD_PLAIN_EXCEPTION"] = str(e)

        # Perturbate the sequence and try to apply again; as we know the
        # code takes care of boundaries, we remove them
        test["FUZZ_SEQ"] = perturbate_element(
            str(test["ORIGINAL_SEQ"])[2:-2], seq_chars
        )
        try:
            alteruphono.forward(alteruphono.Sequence(test["FUZZ_SEQ"]), rule_obj)
        except Exception as e:
            if not isinstance(e, alteruphono.utils.AlteruPhonoError):
                test["SUCCESS"] = False
            test["FORWARD_FUZZ_EXCEPTION"] = str(e)
        try:
            alteruphono.backward(alteruphono.Sequence(test["FUZZ_SEQ"]), rule_obj)
        except Exception as e:
            if not isinstance(e, alteruphono.utils.AlteruPhonoError):
                test["SUCCESS"] = False
            test["BACKWARD_FUZZ_EXCEPTION"] = str(e)

        # Write results and update errors
        writer.writerow(test)
        if not test["SUCCESS"]:
            errors += 1

        # CTRL+C pressed or kill signal?
        if signal_handler.signal:
            break

    # Close logger file
    logger.close()


if __name__ == "__main__":
    main()
