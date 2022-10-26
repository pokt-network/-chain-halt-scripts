from collections import defaultdict
import csv
from dataclasses import dataclass
import json
import pprint

import requests


@dataclass
class Validator:
    address: str
    domain: str
    url: str
    stake_amount: float
    version: str


@dataclass
class Vote:
    partial_addr: str
    vote_data: str

validators = []

with open("versions.json", "r") as v:
    current_versions = json.load(v)

with open("./validators.csv", "r") as nf:
    reader = csv.DictReader(nf)
    for row in reader:
        validators.append(
            Validator(
                address=row["Address"],
                domain=row["Service domain"],
                url=row["Service url"],
                stake_amount=float(row["Stake Amount (POKT)"]),
                version=current_versions[row["Address"]]
            )
        )

validators = sorted(validators, key=lambda x: x.address)
domains = set([val.domain for val in validators])


# versions = {}

# for i, val in enumerate(validators):
    # try:
        # resp = requests.get("{}/v1".format(val.url))
        # if resp.status_code == 200:
            # version = resp.text
        # else:
            # version = "unknown"
    # except:
        # verion = "unknown"
    # print(i, val.address, version)
    # versions[val.address] = version

# print(versions)
# with open("versions.json", "w") as v:
    # json.dump(versions, v)

rounds = {}

for r in ("44", "46"):
    with open("./round{}.json".format(r), "r") as tm:
        data = json.load(tm)


    votes = []
    nils = []

    for i, vote in enumerate(data["prevotes"]):
        fields = vote.split(" ")
        if len(fields) > 1:
            partial_addr = fields[0].split(":")[-1].lower()
            vote = fields[2]
            votes.append(Vote(partial_addr=partial_addr, vote_data=vote))
        else:
            nils.append(validators[i])

    pool_size = sum([validator.stake_amount for validator in validators])

    zero_votes = [vote for vote in votes if vote.vote_data == '000000000000']
    non_nil_non_zero = [vote for vote in votes if vote not in zero_votes]


    nil = defaultdict(lambda: defaultdict(float))
    zero = defaultdict(lambda: defaultdict(float))
    non = defaultdict(lambda: defaultdict(float))


    for validator in validators:
        if any([val.partial_addr in validator.address for val in zero_votes]):
            zero[validator.domain][validator.version] += validator.stake_amount / pool_size
        elif any([val.partial_addr in validator.address for val in non_nil_non_zero]):
            non[validator.domain][validator.version] += validator.stake_amount / pool_size
        elif validator in nils:
            nil[validator.domain][validator.version] += validator.stake_amount / pool_size

    rounds[r] = {"nil": nil, "zero": zero, "non_zero": non}

for domain in domains:
    print("{}".format(domain))
    for r, group in rounds.items():
        print("  - Round {}".format(r))
        nil = group["nil"].get(domain)
        zero = group["zero"].get(domain)
        non = group["non_zero"].get(domain)
        if nil:
            print("    Nil Votes: ")
            for version, v in nil.items():
                print("     - {}: {:.3f}%".format(version if not version.endswith("\n") else version.strip() + " (newline)", v * 100))
        if zero:
            print("    Zero Votes: ")
            for version, v in zero.items():
                print("     - {}: {:.3f}%".format(version if not version.endswith("\n") else version.strip() + " (newline)", v * 100))
        if non:
            print("    Non-Zero Votes: ")
            for version, v in non.items():
                print("     - {}: {:.3f}%".format(version if not version.endswith("\n") else version.strip() + " (newline)", v * 100))

