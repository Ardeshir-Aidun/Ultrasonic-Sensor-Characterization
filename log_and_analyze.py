"""
Ultrasonic Sensor Characterization - Logging & Analysis Script

Two modes:

1. LOGGING MODE: connects to the Arduino over serial, saves everything it
   prints to a timestamped CSV file on my computer. Run this while you
   do your data collection (accuracy sweep or stability test).

2. ANALYSIS MODE: reads a saved CSV log and produces plots + stats
   (accuracy/error, noise std dev, drift over time).

Requires: pyserial, pandas, matplotlib
    
"""

import sys
import csv
import time


def log_serial_to_csv(port, duration_s, output_file, baud=9600):
    import serial

    print(f"Connecting to {port} at {baud} baud...")
    ser = serial.Serial(port, baud, timeout=2)
    time.sleep(2)  # wait for Arduino to reset after serial connection opens

    start = time.time()
    rows_written = 0

    with open(output_file, "w", newline="") as f:
        writer = csv.writer(f)
        print(f"Logging for {duration_s} seconds... (Ctrl+C to stop early)")

        while time.time() - start < duration_s:
            try:
                line = ser.readline().decode("utf-8", errors="ignore").strip()
            except Exception as e:
                print(f"Read error: {e}")
                continue

            if not line:
                continue

            parts = line.split(",")
            writer.writerow(parts)
            rows_written += 1

            if rows_written % 20 == 0:
                elapsed = time.time() - start
                print(f"  {rows_written} rows logged ({elapsed:.0f}s elapsed)")

    ser.close()
    print(f"Done. {rows_written} rows saved to {output_file}")


def analyze_csv(input_file):
    import pandas as pd
    import matplotlib.pyplot as plt

    df = pd.read_csv(input_file)
    # first column is millis, second is distance_cm; header may or may not
    # be present depending on when logging started relative to Arduino reset
    if df.columns[0] != "millis":
        df = pd.read_csv(input_file, names=["millis", "distance_cm"])

    df["distance_cm"] = pd.to_numeric(df["distance_cm"], errors="coerce")
    df = df.dropna(subset=["distance_cm"])
    df["seconds"] = (df["millis"] - df["millis"].iloc[0]) / 1000.0

    mean_d = df["distance_cm"].mean()
    std_d = df["distance_cm"].std()
    n = len(df)

    print(f"\n--- Stats for {input_file} ---")
    print(f"Samples: {n}")
    print(f"Mean distance: {mean_d:.2f} cm")
    print(f"Std dev (noise): {std_d:.3f} cm")
    print(f"Min: {df['distance_cm'].min():.2f} cm, Max: {df['distance_cm'].max():.2f} cm")

    # Simple linear drift check: fit a line to distance vs time
    import numpy as np
    if n > 2:
        slope, intercept = np.polyfit(df["seconds"], df["distance_cm"], 1)
        print(f"Drift rate: {slope*60:.4f} cm/min")

    # Raw readings over time 
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))

    axes[0].plot(df["seconds"], df["distance_cm"], linewidth=0.8)
    axes[0].axhline(mean_d, color="red", linestyle="--", label=f"mean={mean_d:.2f}cm")
    axes[0].set_xlabel("Time (s)")
    axes[0].set_ylabel("Distance (cm)")
    axes[0].set_title("Distance vs Time")
    axes[0].legend()

    # Noise Histogram
    axes[1].hist(df["distance_cm"], bins=30, edgecolor="black")
    axes[1].set_xlabel("Distance (cm)")
    axes[1].set_ylabel("Count")
    axes[1].set_title(f"Noise Distribution (std={std_d:.3f}cm)")

    plt.tight_layout()
    out_png = input_file.rsplit(".", 1)[0] + "_plots.png"
    plt.savefig(out_png, dpi=150)
    print(f"\nPlots saved to {out_png}")
    plt.show()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    mode = sys.argv[1]

    if mode == "log":
        if len(sys.argv) != 5:
            print("Usage: python log_and_analyze.py log <port> <duration_s> <output_file.csv>")
            sys.exit(1)
        _, _, port, duration_s, output_file = sys.argv
        log_serial_to_csv(port, int(duration_s), output_file)

    elif mode == "analyze":
        if len(sys.argv) != 3:
            print("Usage: python log_and_analyze.py analyze <input_file.csv>")
            sys.exit(1)
        analyze_csv(sys.argv[2])

    else:
        print(f"Unknown mode: {mode}")
        print(__doc__)
