import requests
import logging
import base64
import time
import os
import random

def save_binary(blob, label, output_dir="data"):
    """Save the binary blob with its label in the specified directory."""
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, f"{label}_{int(time.time())}.bin")
    with open(file_path, "wb") as f:
        f.write(blob)
    logging.info(f"Saved binary to {file_path}")

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

if __name__ == "__main__":
#pseudo code/thoughts
  #I need to create a labeled dataset which means getting true labels
  #Guess the label for the unknown until known and then save it
  #ALSO, only save the features extracted and not the whole blob which means I need to extract features
  #Repeat until required dataset size reached
  #Train a classifier using dataset features and true labels
  #Use classifier prediction to get 500 in a row
  
    # create the server object
    s = Server()

    for _ in range(100):
        # query the /challenge endpoint
        s.get()

        # choose a random target and /solve
        target = random.choice(s.targets)
        s.post(target)

        s.log.info("Guess:[{: >9}]   Answer:[{: >9}]   Wins:[{: >3}]".format(target, s.ans, s.wins))
    
    # Directory to save binary blobs and labels
    # output_dir = "data"
  
    # #10,000
    # for _ in range(10000):
    #     # query the /challenge endpoint
    #     response = s.get()
    #     count = 0
      
    #     while True:
            
    #       s.post(s.targets[count])
  
    #       s.log.info("Guess:[{: >9}]   Answer:[{: >9}]   Wins:[{: >3}]".format(target, s.ans, s.wins))
      
    #     # Save the binary and its target labels
    #     if s.binary:
    #         for target in s.targets:
    #             save_binary(s.binary, target, output_dir)

        # Optional: Log progress
        # s.log.info("Collected binary and saved with labels: {}".format(s.targets))
      
    if s.hash:
        s.log.info("You win! {}".format(s.hash))
