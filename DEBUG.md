# Task 2 — Debugging the Ploidy Ratio Function

## Problem

The function computes a ploidy ratio from raw sensor channel readings and stores the result using `batch_id`.

The assessment reports two production problems:

1. Ratio values are sometimes exactly double or triple the expected value.
2. A result retrieved for one `batch_id` can belong to an unrelated earlier batch.

## Bugs Identified

### 1. Incorrect baseline selection

The last value in `raw_counts` is explicitly defined as the control channel.

The buggy implementation uses:

```python
baseline = raw_counts[0]
```

This incorrectly assumes that the first reading is the control/baseline. The correct baseline is the last reading:

```python
baseline = raw_counts[-1]
```

Using the wrong baseline can produce incorrect ratios, including substantially different values from the expected result.

### 2. Mutable default argument

The function uses:

```python
results_store={}
```

as a default argument.

Python creates this dictionary once when the function is defined, so subsequent calls reuse the same dictionary. Results from earlier batches therefore remain in the shared dictionary and can appear when processing another `batch_id`, causing cross-batch data leakage.

The fix is:

```python
results_store=None

if results_store is None:
    results_store = {}
```

### 3. Missing input validation

The function does not validate whether `raw_counts` contains enough readings.

At least two values are required: one or more channel readings plus the control reading.

The function should reject:

* Empty input
* A single reading
* Zero control/baseline

For example:

```python
if not raw_counts or len(raw_counts) < 2:
    raise ValueError(
        "Need at least two readings (channels + control)"
    )

if raw_counts[-1] == 0:
    raise ValueError(
        "Control channel reading cannot be zero"
    )
```

Without this validation, the function can produce invalid results or raise unexpected exceptions.

### 4. Missing type validation

The function assumes every value in `raw_counts` is numeric.

Invalid values such as strings can cause unexpected behavior or runtime errors.

Validate the input:

```python
if not all(
    isinstance(value, (int, float))
    for value in raw_counts
):
    raise TypeError("All readings must be numeric")
```

## Correct Implementation

```python
def process_batch_results(
    batch_id,
    raw_counts,
    results_store=None
):
    """
    Computes ploidy ratio from raw sensor readings.

    The last value in raw_counts is the control
    channel reading.
    """

    if results_store is None:
        results_store = {}

    if not raw_counts or len(raw_counts) < 2:
        raise ValueError(
            "Need at least two readings (channels + control)"
        )

    if not all(
        isinstance(value, (int, float))
        for value in raw_counts
    ):
        raise TypeError(
            "All readings must be numeric"
        )

    baseline = raw_counts[-1]

    if baseline == 0:
        raise ValueError(
            "Control channel reading cannot be zero"
        )

    total = sum(raw_counts[:-1])

    ratio = total / baseline

    results_store[batch_id] = ratio

    return results_store
```

## Why the Bugs Explain the Production Symptoms

### Incorrect ratio

The calculation must use the final reading as the control/baseline. Using `raw_counts[0]` instead can divide the total by the wrong value, producing an incorrect ratio.

### Unrelated batch result

The mutable `results_store={}` is shared between function calls. A result from a previous batch remains in the same dictionary, allowing unrelated batch results to be returned later.

## Example

```python
results = {}

results = process_batch_results(
    "SAMPLE001",
    [100, 120, 80, 50],
    results
)

results = process_batch_results(
    "SAMPLE002",
    [90, 110, 100, 50],
    results
)

print(results)
```

The final reading in each input is treated as the control channel, and each result is stored under its own `batch_id`.


