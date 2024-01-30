# ᛤ Runestone Fairdrop Address List Generator

The repo contains instructions to reproduce the list of runestone fairdrop addresses according to the rules defined in LeonidasNFT's [tweet](https://twitter.com/LeonidasNFT/status/1751374137421934872)

Those rules are:
1. Held at least 3 inscriptions

2. At snapshot block height 826,600 (the state of the Bitcoin network after block 826,600 [0000000000000000000262aed91368b42764a507fd68a3b0bcf32791f85dd9eb] was mined but before block 826,601 [00000000000000000000b0621174c1354a8ec55f16115f4a103727f171f34191] was mined)

3. Including cursed inscriptions that are indexed by ord and have a negative inscription number post-Jubilee

4. Excluding inscriptions whose file type starts with either “text/plain” or “application/json” (for example “text/plain;charset=utf-8” inscriptions would be excluded)

An xz compressed archive of the inscription snapshot files has been provided for download at the following link:
```
http://45.61.136.53/inscriptions.tar.xz
```

However, anyone should be able to follow the steps below to produce the exact same files, and validate that these are correct and unmodified.

### Steps to reproduce

#### Sync ord to the correct block height
Start the ord server with the JSON API enabled and let it sync up to block `826600` by setting the `--height-limit` flag. Note that this flag is off by 1, so to sync to `826600` it needs to be set to `826601`

```bash
RUST_LOG=info ./ord --height-limit 826601 server --http --http-port 8080 --enable-json-api
```

#### Run the inscription extractor program
`extract_inscriptions.py` will call the `ord` API for each inscription and extract details about that inscription, including it's address location and the content type.

These details will be written out into JSON Lines (JSONL) files in the `inscriptions` directory

This script requires the `beautifulsoup4` package, so install that first:
```bash
pip install beautifulsoup4
```

Then run the extractor script:
```bash
python extract_inscriptions.py
```

Note that this will take a _long_ time to run. Be patient.

#### Run the fairdrop addresses generator program
The `fairdrop_addresses.py` program reads in all of the inscription metadata in the JSONL files, and processes the data to produce an address list CSV file based on the rules defined for the fairdrop.

This program uses the `pyspark` and `pandas` packages to process the data, so to run you must first install them:
```bash
pip install pyspark
pip install pandas
```

Then run the program:
```bash
python fairdrop_addresses.py
```

This will output a CSV file named `fairdrop_addresses.csv` which is the list of addresses which match the fairdrop rules, as well as a corresponding `fairdrop_addresses.json` JSON file.