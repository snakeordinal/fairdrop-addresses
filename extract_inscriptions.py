import requests
import os
import multiprocessing
import json
import logging
from bs4 import BeautifulSoup

CHUNK_SIZE = 10000
MULTIPROCESSING_POOL_SIZE = 24
SNAPSHOT_BLOCKHEIGHT = 826600
NUM_INSCRIPTIONS = 56612161
NUM_CURSED_INSCRIPTIONS = 472043
ORD_API = "http://localhost:8080"
JSONL_DIRECTORY = "inscriptions"


def get_inscriptions(inscriptions_chunk):
    """
    Calls the ord API to extract inscription metadata
    for a chunk of inscriptions, and writes the output
    as a JSON Lines (JSONL) file.
    """
    file_num = inscriptions_chunk[0]
    start_num = inscriptions_chunk[1]
    file_path = f"{JSONL_DIRECTORY}/{str(file_num).zfill(8)}.jsonl"

    # Skip processing this chunk if we already have the file
    if os.path.isfile(file_path):
        print(f"{file_path} already exists, skipping.")
        return

    # Call API for each inscription in the chunk and collect the metadata
    inscriptions = []
    end_num = start_num + CHUNK_SIZE
    if end_num > NUM_INSCRIPTIONS:
        end_num = NUM_INSCRIPTIONS
    print(f"Extracting {start_num} to {end_num}")
    for n in range(start_num, end_num):
        logging.info(n)
        inscription = requests.get(f"{ORD_API}/inscription/{n}", headers={"Accept": "application/json"}).json()
        
        # The Ord API currently does not return a content type for delegate
        # inscriptions. Work around this by using Beautiful Soup to parse the 
        # inscription HTML page to get the delegate inscription, and pull the content
        # type from the delegate
        content_type = inscription["content_type"]
        if not content_type:
            page = requests.get(f"{ORD_API}/inscription/{n}")
            soup = BeautifulSoup(page.content, "html.parser")
            delegate = soup.find('dt', string='delegate')
            if delegate:
                delegate_inscription_id = delegate.findNext('dd').text
                delegate_inscription = requests.get(f"{ORD_API}/inscription/{delegate_inscription_id}", headers={"Accept": "application/json"}).json()
                content_type = delegate_inscription['content_type']
        
        inscriptions.append(
            {
                "inscription_number": inscription["inscription_number"],
                "inscription_id": inscription["inscription_id"],
                "address": inscription["address"],
                "content_type": content_type,
            }
        )

    # Convert to JSONL and write file
    json_lines = "\n".join([json.dumps(i) for i in inscriptions])
    f = open(file_path, "a")
    f.write(json_lines)
    f.close()


# Check Ord is at the correct blockheight, with the correct inscription counts
ord_status = requests.get(f"{ORD_API}/status", headers={"Accept": "application/json"}).json()
assert (
    ord_status["height"] == SNAPSHOT_BLOCKHEIGHT
), f"Error: Ord is synced to wrong blockheight. Got {ord_status['height']}, expected {SNAPSHOT_BLOCKHEIGHT}"
assert (
    ord_status["blessed_inscriptions"] == NUM_INSCRIPTIONS
), f"Error: Got {ord_status['blessed_inscriptions']} inscriptions, expected {NUM_INSCRIPTIONS}"
assert (
    ord_status["cursed_inscriptions"] == NUM_CURSED_INSCRIPTIONS
), f"Error: Got {ord_status['cursed_inscriptions']} cursed inscriptions, expected {NUM_CURSED_INSCRIPTIONS}"

# Create output directory if it does not exist
if not os.path.exists(JSONL_DIRECTORY):
    os.makedirs(JSONL_DIRECTORY)

# Run the extract in parallel, with each process extracting a chunk
# and outputting that chunk to a file
inscriptions_range = enumerate(range(NUM_CURSED_INSCRIPTIONS * -1, NUM_INSCRIPTIONS, CHUNK_SIZE))
p = multiprocessing.Pool(MULTIPROCESSING_POOL_SIZE)
p.map(get_inscriptions, inscriptions_range)
