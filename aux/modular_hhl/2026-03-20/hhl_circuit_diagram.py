"""Generate a schematic HHL circuit diagram showing the block structure."""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches


def draw_hhl_diagram(out_path: str) -> None:
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.set_xlim(-0.5, 11.5)
    ax.set_ylim(-0.5, 5.5)
    ax.set_aspect("equal")
    ax.axis("off")

    # Wire labels (top to bottom)
    wires = [
        ("ancilla", 4.5, "#e74c3c"),
        ("clock", 2.8, "#2980b9"),
        ("system", 1.0, "#2c3e50"),
    ]

    # Draw wires
    wire_start = 0.8
    wire_end = 10.8
    for label, y, color in wires:
        if label == "clock":
            for dy in [-0.3, 0, 0.3]:
                ax.plot(
                    [wire_start, wire_end], [y + dy, y + dy],
                    color=color, linewidth=0.8, alpha=0.6,
                )
            ax.text(
                0.4, y, label, ha="right", va="center",
                fontsize=10, color=color, fontstyle="italic",
            )
        elif label == "system":
            for dy in [-0.2, 0, 0.2]:
                ax.plot(
                    [wire_start, wire_end], [y + dy, y + dy],
                    color=color, linewidth=0.8, alpha=0.6,
                )
            ax.text(
                0.4, y, label, ha="right", va="center",
                fontsize=10, color=color, fontstyle="italic",
            )
        else:
            ax.plot(
                [wire_start, wire_end], [y, y],
                color=color, linewidth=1.0, alpha=0.6,
            )
            ax.text(
                0.4, y, label, ha="right", va="center",
                fontsize=10, color=color, fontstyle="italic",
            )

    # Block definitions: (x_center, width, y_bottom, height, label, color)
    blocks = [
        (1.6, 1.0, 0.3, 1.4, "State\nPrep", "#27ae60", ["system"]),
        (3.4, 1.8, 0.3, 3.2, "QPE", "#2980b9", ["clock", "system"]),
        (5.6, 1.2, 2.0, 3.2, "C-Rot", "#8e44ad", ["ancilla", "clock"]),
        (7.4, 1.8, 0.3, 3.2, "QPE$^{\\dagger}$", "#2980b9",
         ["clock", "system"]),
        (9.6, 1.0, 3.8, 1.4, "Meas", "#c0392b", ["ancilla"]),
    ]

    for xc, w, yb, h, label, color, _ in blocks:
        rect = mpatches.FancyBboxPatch(
            (xc - w / 2, yb), w, h,
            boxstyle="round,pad=0.08",
            facecolor=color, alpha=0.15,
            edgecolor=color, linewidth=2,
        )
        ax.add_patch(rect)
        ax.text(
            xc, yb + h / 2, label,
            ha="center", va="center",
            fontsize=11, fontweight="bold", color=color,
        )

    # D-1 bracket
    ax.annotate(
        "", xy=(1.0, -0.15), xytext=(10.2, -0.15),
        arrowprops=dict(arrowstyle="|-|", color="#555555", lw=1.5),
    )
    ax.text(
        5.6, -0.45, "D-1: 5 blocks",
        ha="center", va="top", fontsize=10, color="#555555",
    )

    # D-2 annotation on QPE
    ax.annotate(
        "D-2: split into\ncontrolled-U$_k$ + QFT",
        xy=(3.4, 0.3), xytext=(3.4, -0.45),
        fontsize=8, color="#2980b9", ha="center", va="top",
        arrowprops=dict(
            arrowstyle="->", color="#2980b9",
            connectionstyle="arc3,rad=0.0",
        ),
    )

    # Title
    ax.set_title(
        "HHL Algorithm: Block Structure",
        fontsize=14, fontweight="bold", pad=15,
    )

    fig.tight_layout()
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {out_path}")


if __name__ == "__main__":
    draw_hhl_diagram("hhl_block_structure.png")
