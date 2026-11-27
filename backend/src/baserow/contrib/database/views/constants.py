"""Shared constants for the database views layer."""

# Default number of group-by groups per page. Lives in the views layer so the handler
# and the API serializers can share it without the handler importing from the API layer.
GROUP_BY_DATA_DEFAULT_LIMIT = 40

# Maximum user-visible depth for stored view filter groups. Existing deeper trees can
# still be restored because validation is skipped when an explicit primary key is
# supplied by undo/redo or view configuration import.
MAX_FILTER_GROUP_DEPTH = 10
