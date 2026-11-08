# Hardware revisions

No schematics, BOM, PCB files or mechanical drawings exist in this repository. This file records only what the repository states.

| Item | Source | Status |
|---|---|---|
| MCU/IMU board | README, device tree: Seeed XIAO nRF52840 Sense (LSM6DS3 via Zephyr `st,lsm6dsl`) | stated |
| Roll servo | README: MG995 | **inconsistent** with owner notes (MG92B) — to confirm |
| Pitch servo | README: FS90MG | to confirm |
| Servo supply, power budget | — | unknown |
| IMU mounting location / lever arm to pivot | — | unknown; affects whether control is feedback or feed-forward |
| Gimbal geometry, spoon mass | README: 50 g food assumed in simulation | simulation assumption only |

Owner action: add schematic, BOM, photos and measured current draw, and confirm servo models.
