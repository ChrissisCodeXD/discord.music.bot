from copy import copy
from typing import Any, Dict, List, Optional, Tuple


class Equalizer:
    EQUALIZERS = {
        "flat": {
            "name": "Default Equalizer",
            "description": "Just the default EQ nothing changed",
            "bands": [
                (0, 0.0), (1, 0.0), (2, 0.0), (3, 0.0), (4, 0.0),
                (5, 0.0), (6, 0.0), (7, 0.0), (8, 0.0), (9, 0.0),
                (10, 0.0), (11, 0.0), (12, 0.0), (13, 0.0), (14, 0.0)
            ]
        },
        "bass_boost": {
            "name": "Bass Boost",
            "description": "Bass Boost EQ, more bass, more fun ;)",
            "bands": [
                (0, -0.075), (1, 0.125), (2, 0.125), (3, 0.1), (4, 0.1),
                (5, .05), (6, 0.075), (7, 0.0), (8, 0.0), (9, 0.0),
                (10, 0.0), (11, 0.0), (12, 0.125), (13, 0.15), (14, 0.05)
            ]
        },
        "metal": {
            "name": "Metal EQ",
            "description": "EQ for Metal music",
            "bands": [
                (0, 0.0), (1, 0.1), (2, 0.1), (3, 0.15), (4, 0.13),
                (5, 0.1), (6, 0.0), (7, 0.125), (8, 0.175), (9, 0.175),
                (10, 0.125), (11, 0.125), (12, 0.1), (13, 0.075), (14, 0.0)
            ]
        },
        "piano": {
            "name": "Piano EQ",
            "description": "EQ for classic Piano music",
            "bands": [
                (0, -0.25), (1, -0.25), (2, -0.125), (3, 0.0),
                (4, 0.25), (5, 0.25), (6, 0.0), (7, -0.25), (8, -0.25),
                (9, 0.0), (10, 0.0), (11, 0.5), (12, 0.25), (13, -0.025)
            ]
        },
    }

    BANDS = [
        str(i) for i in range(0, 15)
    ]

    HZ_BANDS = {
        "25 Hz": 0, "40 Hz": 1,
        "63 Hz": 2, "100 Hz": 3,
        "160 Hz": 4, "250 Hz": 5,
        "400 Hz": 6, "630 Hz": 7,
        "1k Hz": 8, "1.6k Hz": 9,
        "2.5k Hz": 10, "4k Hz": 11,
        "6.3k Hz": 12, "10k Hz": 13,
        "16k Hz": 14
    }

    GAINS: List[float] = [
        round(i * 0.1, 1) for i in range(-2, 11)
    ]

    def __init__(self, name: str = "Custom", bands: List[Tuple[int, float]] = None, **kwargs):
        self.__default_name: Optional[str] = kwargs.get("default_name", None)
        self.__name = name
        self.__bands = []
        if bands:
            if any((band, gain) for band, gain in bands if band < 0 or band > 15 or gain < -0.25 or gain > 1.0):
                raise ValueError("Equalizer bands must be between 0 and 15 and gains between -0.25 and 1.0")
            self.__bands = bands
            self.__fill_bands()
            extra_bands = {}
            for x in kwargs:
                if x in self.BANDS:
                    extra_bands[x] = (int(x),kwargs.get(x))
            self.edit_bands(extra_bands, change_default=False)
        else:
            self.__build_bands(kwargs)

    def __fill_bands(self):
        if len(self.__bands) < 15:
            tmp_bands = copy(self.__bands)
            self.__bands = self.EQUALIZERS['flat']["bands"]
            for i, e in tmp_bands:
                self.__bands[i] = e

    def __build_bands(self, kwargs):
        for i in range(0, 14):
            self.__bands.append(
                (i, kwargs.get(str(i), 0.0))
            )

    def edit_bands(self, bands: dict, change_default=True):
        if change_default:
            self.__default_name = None
        for i in bands:
            self.__bands[int(i)] = bands.get(i)

    @property
    def bands(self):
        return self.__bands

    @property
    def name(self):
        return self.__name

    @property
    def is_default_eq(self):
        return bool(self.__default_name)

    @classmethod
    def from_equalizer(cls, equ: str):
        match equ:
            case "flat":
                return cls(
                    name=cls.EQUALIZERS["flat"]["name"],
                    bands=cls.EQUALIZERS["flat"]["bands"],
                    default_name=equ
                )
            case "bass_boost":
                return cls(
                    name=cls.EQUALIZERS["bass_boost"]["name"],
                    bands=cls.EQUALIZERS["bass_boost"]["bands"],
                    default_name=equ
                )
            case _:
                raise ValueError(f"Equalizer Preset '{equ}' does not exist!")
