import requests
import logging
import base64
import time
import os
import random
import csv
import math
from collections import Counter

def calculate_entropy(data):
    """Calculate the entropy of binary data."""
    if not data:
        return 0
    counter = Counter(data)
    length = len(data)
    entropy = -sum((count / length) * math.log2(count / length) for count in counter.values())
    return entropy

def byte_frequency(blob):
    """Calculate byte frequency distribution."""
    freq = Counter(blob)
    total_bytes = len(blob)
    return {f"byte_{byte}": count / total_bytes for byte, count in freq.items()}

def opcode_histogram(blob):
    """Generate a simple opcode histogram as a feature (placeholder implementation)."""
    # For simplicity, treat each byte as a potential opcode (this can be refined later with disassembly tools).
    opcodes = Counter(blob)
    top_opcodes = opcodes.most_common(10)
    return {f"opcode_{opcode}": count for opcode, count in top_opcodes}

def extract_features(blob):
    """Extract features from the binary blob."""
    features = {
        "size": len(blob),
        "entropy": calculate_entropy(blob),
        "unique_bytes": len(set(blob)),
    }
    # Add byte frequency and opcode histogram to features
    features.update(byte_frequency(blob))
    features.update(opcode_histogram(blob))
    return features

def save_binary(blob, label, output_dir="C:/Users/loiac/PraetorianChallenges/MachineLearningBinaries/data"):
    """Save the binary blob and its label to the specified directory and record features to a CSV file."""
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, f"{label}_{int(time.time())}.bin")

    # Save the binary file
    with open(file_path, "wb") as f:
        f.write(blob)
    logging.info(f"Saved binary to {file_path}")

    # Extract features and save them to a CSV file
    features = extract_features(blob)
    features.update({"file_path": file_path, "label": label, "timestamp": int(time.time())})

    csv_file = os.path.join(output_dir, "features.csv")
    file_exists = os.path.isfile(csv_file)

    with open(csv_file, mode="a", newline="") as csvfile:
        fieldnames = ["file_path", "label", "timestamp", "size", "entropy", "unique_bytes"] + \
                     [f"byte_{i}" for i in range(256)] + \
                     [f"opcode_{i}" for i in range(256)]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(features)
    logging.info(f"Updated features CSV with file: {file_path}, label: {label}")

logging.basicConfig(level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class Server(object):
    url = 'https://mlb.praetorian.com'
    log = logging.getLogger(__name__)

    def __init__(self):
        self.session = requests.session()
        self.binary  = None
        self.hash    = None
        self.wins    = 0
        self.targets = []

    def _request(self, route, method='get', data=None):
        while True:
            try:
                if method == 'get':
                    r = self.session.get(self.url + route)
                else:
                    r = self.session.post(self.url + route, data=data)
                if r.status_code == 429:
                    raise Exception('Rate Limit Exception')
                if r.status_code == 500:
                    raise Exception('Unknown Server Exception')

                return r.json()
            except Exception as e:
                self.log.error(e)
                self.log.info('Waiting 60 seconds before next request')
                time.sleep(60)

    def get(self):
        r = self._request("/challenge")
        self.targets = r.get('target', [])
        self.binary  = base64.b64decode(r.get('binary', ''))
        return r

    def post(self, target):
        r = self._request("/solve", method="post", data={"target": target})
        self.wins = r.get('correct', 0)
        self.hash = r.get('hash', self.hash)
        self.ans  = r.get('target', 'unknown')
        return r

    def data_collection(self, num_files):
        """Collect and save binary blobs along with their correct labels."""
        for _ in range(num_files):
            response = self.get()

            # Use post to get the correct label
            if self.binary:
                  self.post(random.choice(self.targets))  # Get the answer (self.ans) from the server
                  if self.ans != 'unknown':
                      save_binary(self.binary, self.ans)
                      self.log.info(f"Collected and saved binary with label: {self.ans}")

if __name__ == "__main__":
    # create the server object
    s = Server()

    # Call the data_collection method to collect and save binaries
    num_files_to_collect = 10  # Example: Collect 100 files
    s.data_collection(num_files_to_collect)

    # for _ in range(100):
    #     # query the /challenge endpoint
    #     s.get()

    #     # choose a random target and /solve
    #     target = random.choice(s.targets)
    #     s.post(target)

    #     s.log.info("Guess:[{: >9}]   Answer:[{: >9}]   Wins:[{: >3}]".format(target, s.ans, s.wins))

    if s.hash:
        s.log.info("You win! {}".format(s.hash))
