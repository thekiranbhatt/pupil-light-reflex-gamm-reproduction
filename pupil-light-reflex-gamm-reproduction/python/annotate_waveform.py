"""Draw an annotated version of the average pupil waveform, for readers new to the topic.

The paper's Figure 1 has only a legend and a caption, with no labels on the curve itself.
The annotations here are mine. They mark the stages of the pupil response on the
RAW group averages produced by reproduce_checks.py (not on the model predictions).

All the numbers written on the figure are computed from the data below, not typed by hand.

Usage (from the repository root, after running reproduce_checks.py):
    python python/annotate_waveform.py
"""
import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

wf = pd.read_csv("results/python/mean_waveforms.csv")

INK, MUTED = "#0b0b0b", "#52514e"
PALETTE = {"White": "#52514e", "Red": "#eb6834", "Green": "#2a9d5c", "Blue": "#2a78d6"}

white = wf[wf.CondName == "White"].reset_index(drop=True)
t, y = white.Time_s.values, white["mean"].values

# ---- landmarks of the White curve, all computed from the data -------------
i_low = int(np.argmin(y))
t_low, y_low = t[i_low], y[i_low]

# "Constriction starts": first time the curve is 5% below baseline and stays below
below = np.where(y < -0.05)[0]
t_start = t[below[0]]
y_start = y[below[0]]

# "Half recovered": first time after the lowest point that it has climbed halfway back to zero
after = np.where((t > t_low) & (y > y_low / 2))[0]
t_half, y_half = t[after[0]], y[after[0]]

y_end = y[-1]  # value at 3 s

print(f"constriction passes -5% at {t_start:.2f} s")
print(f"lowest point {y_low:.3f} at {t_low:.2f} s")
print(f"half recovered at {t_half:.2f} s")
print(f"value at 3 s: {y_end:.3f}")

fig, ax = plt.subplots(figsize=(9, 5.4))

# shaded stages
ax.axvspan(0, t_start, color="#f4f3ef", zorder=0)
ax.axvspan(t_start, t_low, color="#e9f0fa", zorder=0)
ax.axvspan(t_low, 3.0, color="#fbefe9", zorder=0)

# the four colours (thin) and White (thick)
for colour in ["Red", "Green", "Blue"]:
    g = wf[wf.CondName == colour]
    ax.plot(g.Time_s, g["mean"], color=PALETTE[colour], lw=1.4, alpha=0.9, label=colour)
ax.plot(t, y, color=PALETTE["White"], lw=2.8, label="White")
ax.axhline(0, color="#bdbbb5", lw=1, ls=(0, (3, 3)))

# stage labels along the top
top = 0.045
ax.text(t_start / 2, top, "1. Waiting", ha="center", va="bottom", fontsize=9, color=INK)
ax.text((t_start + t_low) / 2, top, "2. Constriction\n(pupil shrinks)", ha="center",
        va="bottom", fontsize=9, color=INK)
ax.text((t_low + 3.0) / 2, top, "3. Recovery (pupil widens again in the dark)", ha="center",
        va="bottom", fontsize=9, color=INK)

# marker for the flash itself (0 to 0.1 s), drawn along the bottom edge
ax.fill_between([0, 0.1], -0.415, -0.395, color="#f2c230", zorder=3)
ax.text(0.13, -0.405, "Flash on: 0 to 0.1 s", fontsize=9, color=INK, va="center")

# arrows to key points (text is placed in empty areas, away from the curves)
ax.annotate(f"Pupil already {abs(y_start) * 100:.0f}% smaller\nby {t_start:.2f} s", xy=(t_start, y_start),
            xytext=(0.45, -0.045), fontsize=9, color=MUTED,
            arrowprops=dict(arrowstyle="->", color=MUTED), ha="left", va="center")
ax.annotate(f"Smallest pupil: {y_low:.2f}\n(about {abs(y_low) * 100:.0f}% smaller than baseline)\nat {t_low:.2f} s",
            xy=(t_low, y_low), xytext=(1.4, -0.35), fontsize=9, color=INK,
            arrowprops=dict(arrowstyle="->", color=INK), ha="left", va="center")
ax.annotate(f"Halfway back at {t_half:.2f} s", xy=(t_half, y_half), xytext=(1.95, -0.24),
            fontsize=9, color=MUTED, arrowprops=dict(arrowstyle="->", color=MUTED),
            ha="left", va="center")
ax.annotate(f"Still not fully back at 3 s ({y_end:.2f})", xy=(3.0, y_end), xytext=(1.6, -0.022),
            fontsize=9, color=MUTED, arrowprops=dict(arrowstyle="->", color=MUTED),
            ha="left", va="center")

ax.set_xlim(0, 3.0)
ax.set_ylim(-0.42, 0.11)
ax.set_xlabel("Time after the flash (seconds)")
ax.set_ylabel("Change in pupil size vs. baseline\n(0 = same as before the flash, -0.1 = 10% smaller)")
ax.set_title("What the average pupil does after a brief flash of light\n"
             "(raw averages over 39 people; White flash in bold, other colours thinner)",
             fontsize=11, loc="left")
ax.legend(frameon=False, loc="lower right", fontsize=9)
for side in ("top", "right"):
    ax.spines[side].set_visible(False)
fig.tight_layout()
fig.savefig("figures/annotated_average_waveform.png", dpi=170)
print("saved figures/annotated_average_waveform.png")
