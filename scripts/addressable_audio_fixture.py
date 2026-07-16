from __future__ import annotations

import math

ADDRESSABLE_VERSION = 1
ADDRESSABLE_SAMPLE_RATE = 48_000
ADDRESSABLE_DURATION_MS = 10_000
ADDRESSABLE_FRAME_MS = 50
ADDRESSABLE_TRANSITION_MS = 5
ADDRESSABLE_SEED = 0x05EED123
ADDRESSABLE_BANKS_HZ = (
    (600, 700, 800, 900, 1000, 1100, 1200, 1300),
    (1700, 1800, 1900, 2000, 2100, 2200, 2300, 2400),
    (2900, 3000, 3100, 3200, 3300, 3400, 3500, 3600),
    (4100, 4200, 4300, 4400, 4500, 4600, 4700, 4800),
)
ADDRESSABLE_BANK_NAMES = ("A", "B", "C", "D")
ADDRESSABLE_PLACE_VALUES = (8**3, 8**2, 8, 1)
ADDRESSABLE_COARSE_RMS = 0.24
ADDRESSABLE_CARRIER_RMS = 0.075
ADDRESSABLE_PEAK_DBFS = -3.0
CARRIER_CENTER_HZ = 6000
CARRIER_CHIP_RATE_HZ = 1200
CARRIER_SAMPLES_PER_CHIP = ADDRESSABLE_SAMPLE_RATE // CARRIER_CHIP_RATE_HZ
CARRIER_SINE_Q15 = (0, 23170, 32767, 23170, 0, -23170, -32767, -23170)
CARRIER_SHAPE_Q15 = (
    0,
    53,
    212,
    476,
    843,
    1311,
    1877,
    2536,
    3286,
    4120,
    5034,
    6022,
    7077,
    8192,
    9360,
    10574,
    11825,
    13106,
    14409,
    15724,
    17043,
    18358,
    19661,
    20942,
    22193,
    23407,
    24575,
    25690,
    26745,
    27733,
    28647,
    29481,
    30231,
    30890,
    31456,
    31924,
    32291,
    32555,
    32714,
    32767,
)


def frame_digits(frame_index: int) -> tuple[int, ...]:
    return tuple((frame_index // place) % 8 for place in ADDRESSABLE_PLACE_VALUES)


def _coarse_layer(sample_count: int) -> list[float]:
    frame_samples = ADDRESSABLE_SAMPLE_RATE * ADDRESSABLE_FRAME_MS // 1000
    transition_samples = ADDRESSABLE_SAMPLE_RATE * ADDRESSABLE_TRANSITION_MS // 1000
    frame_count = sample_count // frame_samples
    digits = [frame_digits(index) for index in range(frame_count)]
    result: list[float] = []
    tone_amplitude = ADDRESSABLE_COARSE_RMS / math.sqrt(2)

    for index in range(sample_count):
        frame_index, offset = divmod(index, frame_samples)
        current = digits[frame_index]
        in_transition = frame_index > 0 and offset < transition_samples
        old_gain = 0.0
        new_gain = 0.0
        if in_transition:
            progress = offset / (transition_samples - 1)
            old_gain = math.cos(math.pi * progress / 2)
            new_gain = math.sin(math.pi * progress / 2)
        value = 0.0
        for bank_index, bank in enumerate(ADDRESSABLE_BANKS_HZ):
            frequency = bank[current[bank_index]]
            phase = 2 * math.pi * frequency * index / ADDRESSABLE_SAMPLE_RATE
            if not in_transition:
                value += math.sin(phase) * tone_amplitude
                continue
            old_frequency = bank[digits[frame_index - 1][bank_index]]
            if old_frequency == frequency:
                value += math.sin(phase) * tone_amplitude
            else:
                old_phase = (
                    2 * math.pi * old_frequency * index / ADDRESSABLE_SAMPLE_RATE
                )
                value += (
                    math.sin(old_phase) * old_gain + math.sin(phase) * new_gain
                ) * tone_amplitude
        result.append(value)

    # Crossfades perturb finite-window energy slightly; normalize each complete
    # code frame so all absolute positions retain the same coarse-layer RMS.
    for start in range(0, sample_count, frame_samples):
        stop = start + frame_samples
        rms = math.sqrt(
            sum(value * value for value in result[start:stop]) / frame_samples
        )
        scale = ADDRESSABLE_COARSE_RMS / rms
        result[start:stop] = (value * scale for value in result[start:stop])
    return result


def _prbs31_signs(count: int) -> list[int]:
    # PRBS31 uses the primitive polynomial x^31 + x^28 + 1. The explicit
    # shift/XOR recurrence makes the carrier independent of stdlib PRNG changes.
    state = ADDRESSABLE_SEED
    output: list[int] = []
    for _ in range(count):
        output.append(1 if state & (1 << 30) else -1)
        feedback = ((state >> 30) ^ (state >> 27)) & 1
        state = ((state << 1) & 0x7FFFFFFF) | feedback
    return output


def _carrier_layer(sample_count: int) -> list[float]:
    chip_count = math.ceil(sample_count / CARRIER_SAMPLES_PER_CHIP) + 1
    signs = _prbs31_signs(chip_count)
    result: list[float] = []
    for index in range(sample_count):
        chip, offset = divmod(index, CARRIER_SAMPLES_PER_CHIP)
        weight = CARRIER_SHAPE_Q15[offset]
        modulation = (signs[chip] * (32767 - weight) + signs[chip + 1] * weight) / 32767
        carrier = CARRIER_SINE_Q15[index % len(CARRIER_SINE_Q15)] / 32767
        result.append(modulation * carrier)

    mean = math.fsum(result) / sample_count
    centered = [value - mean for value in result]
    rms = math.sqrt(math.fsum(value * value for value in centered) / sample_count)
    return [value * ADDRESSABLE_CARRIER_RMS / rms for value in centered]


def _epoch_chirp(index: int) -> float:
    chirp_samples = ADDRESSABLE_SAMPLE_RATE * 20 // 1000
    offset = index % ADDRESSABLE_SAMPLE_RATE
    if offset >= chirp_samples:
        return 0.0
    time_s = offset / ADDRESSABLE_SAMPLE_RATE
    duration_s = chirp_samples / ADDRESSABLE_SAMPLE_RATE
    envelope = math.sin(math.pi * time_s / duration_s) ** 2
    start_hz, end_hz = 800, 1400
    sweep_hz_s = (end_hz - start_hz) / duration_s
    phase = 2 * math.pi * (start_hz * time_s + sweep_hz_s * time_s**2 / 2)
    return 0.035 * envelope * math.sin(phase)


def addressable_samples() -> tuple[bytes, dict[str, object]]:
    sample_count = ADDRESSABLE_SAMPLE_RATE * ADDRESSABLE_DURATION_MS // 1000
    coarse = _coarse_layer(sample_count)
    carrier = _carrier_layer(sample_count)
    mixed = [coarse[i] + carrier[i] + _epoch_chirp(i) for i in range(sample_count)]
    peak = max(abs(value) for value in mixed)
    peak_target = 10 ** (ADDRESSABLE_PEAK_DBFS / 20)
    scale = peak_target / peak
    pcm_values = [round(value * scale * 32767) for value in mixed]
    output = bytearray()
    for value in pcm_values:
        output.extend(value.to_bytes(2, "little", signed=True))

    measured_peak = max(abs(value) for value in pcm_values) / 32767
    metadata: dict[str, object] = {
        "version": ADDRESSABLE_VERSION,
        "seed": ADDRESSABLE_SEED,
        "seedHex": f"0x{ADDRESSABLE_SEED:08X}",
        "sampleRateHz": ADDRESSABLE_SAMPLE_RATE,
        "channels": 1,
        "sampleWidthBits": 16,
        "durationMs": ADDRESSABLE_DURATION_MS,
        "frameDurationMs": ADDRESSABLE_FRAME_MS,
        "frameCount": ADDRESSABLE_DURATION_MS // ADDRESSABLE_FRAME_MS,
        "transitionMs": ADDRESSABLE_TRANSITION_MS,
        "radix": 8,
        "bankNames": list(ADDRESSABLE_BANK_NAMES),
        "banksHz": [list(bank) for bank in ADDRESSABLE_BANKS_HZ],
        "digitOrder": {
            "encoding": "base-8-most-significant-bank-first",
            "banksMostToLeastSignificant": list(ADDRESSABLE_BANK_NAMES),
            "placeValues": list(ADDRESSABLE_PLACE_VALUES),
        },
        "coarse": {
            "tonesPerFrame": 4,
            "crossfade": "equal-power-raised-cosine",
            "frameRmsLinear": ADDRESSABLE_COARSE_RMS * scale,
            "phase": "global-continuous",
        },
        "carrier": {
            "algorithm": "prbs31-x31-x28-1-bpsk-raised-cosine-v1",
            "centerFrequencyHz": CARRIER_CENTER_HZ,
            "chipRateHz": CARRIER_CHIP_RATE_HZ,
            "samplesPerChip": CARRIER_SAMPLES_PER_CHIP,
            "nominalBandHz": [4800, 7200],
            "periodChips": 2**31 - 1,
            "periodSeconds": (2**31 - 1) / CARRIER_CHIP_RATE_HZ,
            "rmsLinear": ADDRESSABLE_CARRIER_RMS * scale,
        },
        "chirp": {
            "amplitudeLinearBeforePeakNormalization": 0.035,
            "durationMs": 20,
            "frequenciesHz": [800, 1400],
            "intervalMs": 1000,
        },
        "peak": {
            "targetDbfs": ADDRESSABLE_PEAK_DBFS,
            "measuredDbfs": 20 * math.log10(measured_peak),
        },
    }
    return bytes(output), metadata
