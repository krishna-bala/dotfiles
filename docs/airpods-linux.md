# AirPods Pro Setup on Linux

Guide for setting up AirPods Pro on Linux machines with Bluetooth.

## Prerequisites

- BlueZ (Bluetooth stack)
- PulseAudio or PipeWire
- Optional: Blueman (GUI manager)

```bash
# Ubuntu/Debian
sudo apt install bluez pulseaudio-module-bluetooth blueman

# Arch
sudo pacman -S bluez bluez-utils pulseaudio-bluetooth blueman
```

## Pairing

1. Put AirPods in case, open lid
2. Hold button on back of case until light flashes white
3. Pair via Blueman or bluetoothctl:

```bash
bluetoothctl
# In bluetoothctl shell:
scan on
# Wait for AirPods to appear, note the MAC address
pair XX:XX:XX:XX:XX:XX
trust XX:XX:XX:XX:XX:XX
connect XX:XX:XX:XX:XX:XX
```

## Audio Profiles

AirPods support two Bluetooth profiles:

| Profile | Quality | Microphone | Use Case |
|---------|---------|------------|----------|
| A2DP (a2dp_sink) | High (SBC/AAC) | No | Music, videos |
| HFP (handsfree_head_unit) | Lower (mSBC) | Yes | Calls, voice input |

This is a Bluetooth limitation, not a Linux issue. You cannot have high-quality audio and microphone simultaneously.

## Switching Profiles

First, find your card name:

```bash
pactl list cards short | grep bluez
```

Switch to HFP (microphone enabled):

```bash
pactl set-card-profile bluez_card.XX_XX_XX_XX_XX_XX handsfree_head_unit
```

Switch to A2DP (high quality audio):

```bash
pactl set-card-profile bluez_card.XX_XX_XX_XX_XX_XX a2dp_sink
```

Replace `XX_XX_XX_XX_XX_XX` with your AirPods MAC address (colons replaced with underscores).

## Shell Aliases

Add to your bash aliases for convenience:

```bash
# Get your AirPods card name dynamically
alias airpods-mic='pactl set-card-profile $(pactl list cards short | grep bluez | cut -f2) handsfree_head_unit'
alias airpods-hifi='pactl set-card-profile $(pactl list cards short | grep bluez | cut -f2) a2dp_sink'
```

## Troubleshooting

### AirPods not connecting automatically

```bash
bluetoothctl
trust XX:XX:XX:XX:XX:XX
```

### Poor audio quality

Check codec in use:

```bash
pactl list cards | grep -A5 bluez | grep codec
```

- `sbc` - Standard quality
- `aac` - Better quality (if supported)
- `mSBC` - Used in HFP mode (expected to be lower quality)

### No sound after connecting

Restart PulseAudio/PipeWire:

```bash
# PulseAudio
pulseaudio -k && pulseaudio --start

# PipeWire
systemctl --user restart pipewire pipewire-pulse
```

### Microphone not showing up

Ensure you're on HFP profile (see Switching Profiles above).
