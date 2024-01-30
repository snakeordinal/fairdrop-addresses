from pyspark.sql import SparkSession

NUM_INSCRIPTIONS = 56612161
NUM_CURSED_INSCRIPTIONS = 472043

# Create Spark session
spark = SparkSession.builder.appName("Fairdrop Addresses").master("local").getOrCreate()

# Read all inscription data from extracted jsonl files
df = spark.read.json("inscriptions/*.jsonl")
df.createOrReplaceTempView("all_inscriptions")

# Validate the data
num_inscriptions = spark.sql(
    "SELECT COUNT(DISTINCT inscription_id) as n FROM all_inscriptions WHERE inscription_number >=0"
).collect()[0]["n"]
num_cursed_inscriptions = spark.sql(
    "SELECT COUNT(DISTINCT inscription_id) as n FROM all_inscriptions WHERE inscription_number <0"
).collect()[0]["n"]
assert num_inscriptions == NUM_INSCRIPTIONS, f"Error: expected {NUM_INSCRIPTIONS} inscriptions, got {num_inscriptions}"
assert (
    num_cursed_inscriptions == NUM_CURSED_INSCRIPTIONS
), f"Error: expected {NUM_CURSED_INSCRIPTIONS}, got {num_cursed_inscriptions}"

# Get addresses which have 3 or more non text/json inscriptions
fairdrop_addresses = spark.sql(
    """
    SELECT
        address,
        COUNT(DISTINCT inscription_id) as num_inscriptions
    FROM 
        all_inscriptions
    WHERE 
            content_type NOT LIKE 'text/plain%'
        AND content_type NOT LIKE 'application/json%'
        AND address IS NOT NULL
        AND content_type IS NOT NULL
    GROUP BY address
    HAVING COUNT(DISTINCT inscription_id) >= 3
    ORDER BY num_inscriptions DESC, address
"""
)

# Output to CSV & JSON file
fairdrop_addresses = fairdrop_addresses.toPandas()
fairdrop_addresses.to_csv(path_or_buf="fairdrop_addresses.csv", index=False)
fairdrop_addresses.to_json(path_or_buf="fairdrop_addresses.json", orient="records")
