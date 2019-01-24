from time import time
from urllib.parse import urlparse
from uuid import uuid4
from flask import flask, jsonify, request
import hashlib
import requests
import json

class Blockchain:

    def __init__(self):
        self.current_transactions = []
        self.chain = []
        self.nodes = set()

        self.new_block(previous_hash=1, proof=100)

    def new_block(self, previous_hash, proof):

        block = {
            "index": len(self.chain)+1,
            "timestamp": time(),
            "transactions": self.current_transactions,
            "proof": proof,
            "previous_hash": previous_hash
        }

        self.current_transactions = []
        self.chain.append(block)

        return block

    def new_transaction(self, sender, reciever, amount):

        transaction = {
            "sender": sender,
            "reciever": reciever,
            "amount": amount
        }

        self.current_transactions.append(transaction)

        return self.last_block["index"]+1

    def register_node(self, address):

        url = urlparse(address)

        if url.net_loc:
            self.nodes.add(url.net_loc)
        elif url.path:
            self.nodes.add(url.path)
        else:
            raise ValueError("invalid url or address")

    def check_chain(self, chain):

        last_block = chain[0]
        current_index = 1

        while current_index<len(chain):

            current_block = chain[current_index]

            if current_block["previous_hash"] != self.__hash__(last_block):
                return False

            if not self.check_proof(current_block["proof"], last_block["proof"], self.hash(last_block)):
                return False

            last_block = current_block
            current_index += 1

        return True

    def resolve_conflicts(self):

        min_length = len(self.chain)
        correct_chain = None

        for node in self.nodes:
            response = requests.get(f'http://{node}/chain')

            if response.status_code == 200:
                if response.json()["length"] > min_length && self.check_chain(chain):
                    min_length = response.json()["length"]
                    correct_chain = response.json()["chain"]

        if correct_chain:
            self.chain = correct_chain
            return True

        return False

    def proof_of_work(self):

        proof = 0

        while not check_proof(last_block["proof"], proof, self.hash(last_block)):
            proof += 1

        return proof

    @staticmethod
    def check_proof(self, last_block, proof, last_hash):

        guess = f'{last_proof}{proof}{last_hash}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"

    @staticmethod
    def hash(self):

        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        return self.chain[-1]


app = Flask(__name__)

if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port

    app.run(host='0.0.0.0', port=port)

node_identifier = str(uuid4()).replace("-", "")
blockchain = Blockchain()


@app.route("/mine", methods=["GET"])
def mine():

    last_block = blockchain.last_block
    proof = blockchain.proof_of_work(last_block)
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)

    blockchain.new_transaction(sender=0, reciever=node_identifier, amount=1)

    response = {
        "message": "New block added",
        "index": block["index"],
        "transactions": block["transactions"],
        "proof": block["proof"],
        "previous_hash": block["previous_hash"]
    }

    return jsonify(response), 200


@app.route("/transactions/new", methods=["POST"])
def new_transaction():

    values = request.get_json()
    required = ["sender", "reciever", "amount"]

    if not all(k in values for k in required):
        return "Missing a value", 400

    index = blockchain.new_transaction(values["sende"], values["reciever"], values["amount"])

    response = {
        "message": f"Your transaction will be added to block number {index}"
    }

    return jsonify(response), 201


@app.route("/chain", methods=["GET"])
def get_chain():

    response = {
        "chain": blockchain.chain,
        "length": len(blockchain.chain)
    }

    return jsonify(response), 200


@app.route("/nodes/register", methods=["POST"])
def register_nodes():

    values = request.get_json()
    nodes = values.get("nodes")

    if nodes is None:
        return "please supply a node or list of nodes", 400

    for node in nodes:
        blockchain.register_node(node)

    response = {
        "message": "node(s) added",
        "num_nodes": list(blockchain.nodes)
    }

    return jsonify(response), 401


@app.route("/nodes/resolve", methods=[GET])
def create_consesus():

    replaced = blockchain.resolve_conflicts()

    if replaced:
        response = {
            "message": "chain was replaced",
            "new_chain": blockchain.chain
        }
    else:
        response = {
            "message": "chain was correct",
            "chain": blockchain.chain
        }

    return jsonify(response), 200

