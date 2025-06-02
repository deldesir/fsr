# Publisher Roles
ROLE_NON_PIONEER = "Non-Pioneer"
ROLE_AUXILIARY_PIONEER = "Auxiliary Pioneer"
ROLE_REGULAR_PIONEER = "Regular Pioneer"
ROLE_SPECIAL_PIONEER = "Special Pioneer"

# Pioneer Status Keywords (for matching in pioneer field from JSON report)
# These are typically checked against a lowercased version of the input field.
PIONEER_KEYWORD_AUXILIARY = "auxiliary"
PIONEER_KEYWORD_REGULAR = "regular"
PIONEER_KEYWORD_SPECIAL = "special"

# List of all pioneer roles, can be useful for checking if a role is any type of pioneer
ALL_PIONEER_ROLES = [
    ROLE_AUXILIARY_PIONEER,
    ROLE_REGULAR_PIONEER,
    ROLE_SPECIAL_PIONEER,
]
