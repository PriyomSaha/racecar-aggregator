import hashlib

def generate_id(prefix: str, url: str) -> str:
    """Generate a unique ID by hashing the URL and prefixing it.

    Args:
        prefix (str): The prefix to append before the hash.
        url (str): The URL to hash.

    Returns:
        str: The generated ID.
    """
    hash_obj = hashlib.sha256(url.encode())
    return prefix + hash_obj.hexdigest()