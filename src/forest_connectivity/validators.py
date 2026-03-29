from rest_framework import serializers

# Minimal placeholder list of known valid blocks.
# In production, replace this with a database query joining state/district/block schemas
# or external API call.
KNOWN_BLOCKS = {
    "jharkhand": {
        "ranchi": ["kanke", "namkum", "ormanji"],
        "west singhbhum": ["saranda", "chaibasa"]
    }
}

def validate_location(state: str, district: str, block: str):
    """
    Validates that the provided state, district, and block exist in our known dictionary.
    """
    state_norm = state.strip().lower()
    district_norm = district.strip().lower()
    block_norm = block.strip().lower()

    if state_norm not in KNOWN_BLOCKS:
        raise serializers.ValidationError({"state": f"State '{state}' is not recognized."})

    state_dict = KNOWN_BLOCKS[state_norm]
    
    if district_norm not in state_dict:
        raise serializers.ValidationError({"district": f"District '{district}' not recognized in '{state}'."})

    valid_blocks = state_dict[district_norm]

    if block_norm not in valid_blocks:
        raise serializers.ValidationError({"block": f"Block '{block}' not recognized in '{district}'. Known: {valid_blocks}"})
