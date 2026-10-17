import random
import secrets


def create_random_generator(seed: int | None = None) -> tuple[int, random.Random]:
    """Return the seed and generator so the run can be reproduced later."""
    actual_seed = secrets.randbits(63) if seed is None else seed
    if not 0 <= actual_seed < 2**63:
        raise ValueError("Seed musi być liczbą z zakresu 0–2**63-1.")
    return actual_seed, random.Random(actual_seed)
