"""
Script to generate publication-grade Figure 1: System Architecture of the Proposed FCIL Framework.
Generates:
  - Paper/figures/fig1_architecture.pdf
  - Paper/figures/fig1_architecture.png
  - report/figures/fig1_architecture.pdf
  - report/figures/fig1_architecture.png
"""

import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def draw_architecture_diagram():
    fig, ax = plt.subplots(figsize=(16, 6.5), dpi=300)
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 6.5)
    ax.axis("off")

    # Font and styling
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial"]

    # Color Palette (Professional Nature/IEEE Style)
    C_BLUE   = "#EBF5FB"  # Telemetry / Scaler
    B_BLUE   = "#2980B9"
    C_PURPLE = "#F4ECF7"  # FCILNet Backbone
    B_PURPLE = "#8E44AD"
    C_GREEN  = "#EAFAF1"  # Dynamic Head
    B_GREEN  = "#27AE60"
    C_ORANGE = "#FEF9E7"  # Edge Clients & Server
    B_ORANGE = "#D35400"
    C_RED    = "#FDEDEC"  # Proposed MALFSIL Defense
    B_RED    = "#C0392B"
    C_GRAY   = "#F8F9F9"
    B_GRAY   = "#7F8C8D"

    # =========================================================================
    # STAGE (a): Dynamic Telemetry & Train-Fitted Scaling
    # =========================================================================
    box_a = patches.FancyBboxPatch((0.3, 0.8), 3.2, 5.0, boxstyle="round,pad=0.15",
                                  facecolor=C_BLUE, edgecolor=B_BLUE, linewidth=1.8)
    ax.add_patch(box_a)
    ax.text(1.9, 5.45, "(a) Dynamic Telemetry & Scaling", fontsize=11, fontweight="bold",
            color=B_BLUE, ha="center")

    # Telemetry details
    t_box = patches.FancyBboxPatch((0.5, 2.7), 2.8, 2.5, boxstyle="round,pad=0.1",
                                  facecolor="#FFFFFF", edgecolor="#BDC3C7", linewidth=1.0)
    ax.add_patch(t_box)
    ax.text(1.9, 4.95, "CIC-AndMal-2020 (141d)", fontsize=10, fontweight="bold", ha="center")
    
    feats = [
        r"$\bullet$ Memory Footprint (23d)",
        r"  $\cdot$ PSS, Clean/Dirty, Heap",
        r"$\bullet$ API & Syscalls (95d)",
        r"  $\cdot$ Shell, Native Lib, Binder",
        r"$\bullet$ Network & IPC (23d)",
        r"  $\cdot$ Total RX, Activity States",
    ]
    y_pos = 4.6
    for f in feats:
        font_s = 8.5 if r"$\cdot$" in f else 9
        color_s = "#555555" if r"$\cdot$" in f else "#111111"
        ax.text(0.65, y_pos, f, fontsize=font_s, color=color_s, ha="left")
        y_pos -= 0.32

    # Scaler
    s_box = patches.FancyBboxPatch((0.5, 1.1), 2.8, 1.25, boxstyle="round,pad=0.1",
                                  facecolor="#D4EFDF", edgecolor=B_GREEN, linewidth=1.2)
    ax.add_patch(s_box)
    ax.text(1.9, 2.05, "Train-Fitted Scaling", fontsize=9.5, fontweight="bold", color="#196F3D", ha="center")
    ax.text(1.9, 1.6, r"$\tilde{\mathbf{x}} = (\mathbf{x} - \boldsymbol{\mu}_{\mathrm{train}}) / (\boldsymbol{\sigma}_{\mathrm{train}} + \epsilon)$",
            fontsize=9, ha="center", color="#145A32")
    ax.text(1.9, 1.25, "Zero Data-Leakage Guarantee", fontsize=7.5, fontstyle="italic", ha="center", color="#27AE60")

    # Arrow a -> b
    ax.annotate("", xy=(3.9, 3.3), xytext=(3.5, 3.3),
                arrowprops=dict(arrowstyle="->", lw=2.2, color=B_BLUE))

    # =========================================================================
    # STAGE (b): FCILNet Neural Backbone (Hybrid TCN-CNN)
    # =========================================================================
    box_b = patches.FancyBboxPatch((3.9, 0.8), 3.5, 5.0, boxstyle="round,pad=0.15",
                                  facecolor=C_PURPLE, edgecolor=B_PURPLE, linewidth=1.8, linestyle="--")
    ax.add_patch(box_b)
    ax.text(5.65, 5.45, "(b) FCILNet Neural Backbone", fontsize=11, fontweight="bold",
            color=B_PURPLE, ha="center")

    # 1D-CNN Stage
    cnn_box = patches.FancyBboxPatch((4.1, 3.9), 3.1, 1.3, boxstyle="round,pad=0.08",
                                     facecolor="#FFFFFF", edgecolor="#BDC3C7", linewidth=1.0)
    ax.add_patch(cnn_box)
    ax.text(5.65, 4.95, "Multi-Scale 1D-CNN Stage", fontsize=9.5, fontweight="bold", ha="center")
    ax.text(5.65, 4.55, r"Parallel Conv1D ($k=3$ & $k=5$)", fontsize=8.5, ha="center")
    ax.text(5.65, 4.15, r"GELU + BatchNorm + MaxPool ($s=2$)", fontsize=8, color="#555555", ha="center")

    # Down arrow inside backbone
    ax.annotate("", xy=(5.65, 3.55), xytext=(5.65, 3.85),
                arrowprops=dict(arrowstyle="->", lw=1.5, color=B_PURPLE))

    # Dilated TCN Stage
    tcn_box = patches.FancyBboxPatch((4.1, 2.3), 3.1, 1.2, boxstyle="round,pad=0.08",
                                     facecolor="#FFFFFF", edgecolor="#BDC3C7", linewidth=1.0)
    ax.add_patch(tcn_box)
    ax.text(5.65, 3.2, "Dilated Residual TCN Stage", fontsize=9.5, fontweight="bold", ha="center")
    ax.text(5.65, 2.8, r"Causal Dilated Blocks ($d \in \{1, 2, 4\}$)", fontsize=8.5, ha="center")
    ax.text(5.65, 2.45, r"Captures Temporal & Behavioral Logs", fontsize=8, color="#555555", ha="center")

    # Down arrow inside backbone
    ax.annotate("", xy=(5.65, 1.95), xytext=(5.65, 2.25),
                arrowprops=dict(arrowstyle="->", lw=1.5, color=B_PURPLE))

    # Adaptive Pooling Stage
    pool_box = patches.FancyBboxPatch((4.1, 1.05), 3.1, 0.85, boxstyle="round,pad=0.08",
                                      facecolor="#E8DAEF", edgecolor=B_PURPLE, linewidth=1.0)
    ax.add_patch(pool_box)
    ax.text(5.65, 1.6, "Adaptive Average Pooling", fontsize=9, fontweight="bold", ha="center")
    ax.text(5.65, 1.25, r"Latent Embedding $\mathbf{z} \in \mathbb{R}^{d}$ ($d=64$)", fontsize=8.5,
            color="#4A235A", ha="center")

    # Arrow b -> c
    ax.annotate("", xy=(7.8, 3.3), xytext=(7.4, 3.3),
                arrowprops=dict(arrowstyle="->", lw=2.2, color=B_PURPLE))

    # =========================================================================
    # STAGE (c): Dynamic Expanding Classification Head
    # =========================================================================
    box_c = patches.FancyBboxPatch((7.8, 0.8), 3.2, 5.0, boxstyle="round,pad=0.15",
                                  facecolor=C_GREEN, edgecolor=B_GREEN, linewidth=1.8)
    ax.add_patch(box_c)
    ax.text(9.4, 5.45, "(c) Dynamic Expanding Head", fontsize=11, fontweight="bold",
            color=B_GREEN, ha="center")

    # 5-Task expansion representation
    head_box = patches.FancyBboxPatch((8.0, 2.8), 2.8, 2.4, boxstyle="round,pad=0.1",
                                      facecolor="#FFFFFF", edgecolor="#BDC3C7", linewidth=1.0)
    ax.add_patch(head_box)
    ax.text(9.4, 4.95, "5-Task Class Expansion", fontsize=9.5, fontweight="bold", ha="center")

    tasks = [
        (r"Task 1 ($\mathcal{T}_0$):", "3 classes (Benign, PUA, Backdoor)"),
        (r"Task 2 ($\mathcal{T}_1$):", "6 classes (+3 Bank, Spy, Adware)"),
        (r"Task 3 ($\mathcal{T}_2$):", "9 classes (+3 Trojan, Risk, etc.)"),
        (r"Task 4 ($\mathcal{T}_3$):", "12 classes (+3 Ransom, Drop, Inf.)"),
        (r"Task 5 ($\mathcal{T}_4$):", "15 classes (+3 SMS, Scare, 0-Day)"),
    ]
    y_pos = 4.55
    for t_title, t_desc in tasks:
        ax.text(8.15, y_pos, t_title, fontsize=8, fontweight="bold", color="#196F3D", ha="left")
        ax.text(8.15, y_pos - 0.18, t_desc, fontsize=7.5, color="#555555", ha="left")
        y_pos -= 0.42

    # Dynamic Weight Preservation box
    w_box = patches.FancyBboxPatch((8.0, 1.1), 2.8, 1.45, boxstyle="round,pad=0.08",
                                   facecolor="#D5F5E3", edgecolor=B_GREEN, linewidth=1.0)
    ax.add_patch(w_box)
    ax.text(9.4, 2.25, "Parameter Allocation", fontsize=9, fontweight="bold", ha="center")
    ax.text(9.4, 1.85, r"$\mathbf{W}_t = [\mathbf{W}_{t-1}^T, \mathbf{W}_{\mathrm{new}}^T]^T$",
            fontsize=9, ha="center", color="#145A32")
    ax.text(9.4, 1.45, "Historical Weights Preserved", fontsize=7.5, fontstyle="italic",
            ha="center", color="#27AE60")
    ax.text(9.4, 1.2, r"Linear or Cosine Normalized: $s \cdot \frac{\mathbf{w}^T \mathbf{z}}{\|\mathbf{w}\| \|\mathbf{z}\|}$",
            fontsize=7.2, ha="center", color="#1E8449")

    # Arrow c -> d
    ax.annotate("", xy=(11.4, 3.3), xytext=(11.0, 3.3),
                arrowprops=dict(arrowstyle="->", lw=2.2, color=B_GREEN))

    # =========================================================================
    # STAGE (d): Proposed Federated Continual Learning (FL-MALFSIL)
    # =========================================================================
    box_d = patches.FancyBboxPatch((11.4, 0.8), 4.3, 5.0, boxstyle="round,pad=0.15",
                                  facecolor=C_ORANGE, edgecolor=B_ORANGE, linewidth=1.8)
    ax.add_patch(box_d)
    ax.text(13.55, 5.45, "(d) Proposed FCIL Framework (FL-MALFSIL)", fontsize=10.5,
            fontweight="bold", color=B_ORANGE, ha="center")

    # Client Box
    client_box = patches.FancyBboxPatch((11.6, 2.65), 3.9, 2.55, boxstyle="round,pad=0.08",
                                        facecolor="#FFFFFF", edgecolor=B_RED, linewidth=1.4)
    ax.add_patch(client_box)
    ax.text(13.55, 4.95, "Edge Clients ($K=20, 50$)", fontsize=9.5, fontweight="bold",
            color=B_RED, ha="center")
    ax.text(13.55, 4.65, r"Dirichlet Non-IID Label Skew ($\alpha = 0.5$)", fontsize=8,
            color="#7B241C", ha="center")

    # Proposed Triad
    triad_bg = patches.FancyBboxPatch((11.75, 2.8), 3.6, 1.65, boxstyle="round,pad=0.05",
                                     facecolor=C_RED, edgecolor=B_RED, linewidth=0.8)
    ax.add_patch(triad_bg)
    ax.text(13.55, 4.25, r"$\mathbf{Three}$-$\mathbf{Tier\ Continual\ Defense\ (Ours)}$",
            fontsize=8.5, fontweight="bold", color=B_RED, ha="center")
    ax.text(11.9, 3.85, r"1. Compact Herding Replay ($\mathcal{M}, m=20$)", fontsize=7.8, color="#922B21")
    ax.text(11.9, 3.45, r"2. Adaptive Logit Distillation ($\mathcal{L}_{\mathrm{distill}}$)", fontsize=7.8, color="#922B21")
    ax.text(11.9, 3.05, r"3. Global Prototype Alignment ($\mathcal{L}_{\mathrm{proto}}$)", fontsize=7.8, color="#922B21")

    # Bidirectional communication arrows
    ax.annotate("", xy=(13.0, 2.2), xytext=(13.0, 2.6),
                arrowprops=dict(arrowstyle="->", lw=1.8, color=B_ORANGE))
    ax.text(12.75, 2.4, r"$\Delta\boldsymbol{\theta}, \mathbf{p}_c^{(k)}$", fontsize=7.5,
            color=B_ORANGE, ha="right")

    ax.annotate("", xy=(14.1, 2.6), xytext=(14.1, 2.2),
                arrowprops=dict(arrowstyle="->", lw=1.8, color=B_BLUE))
    ax.text(14.35, 2.4, r"$\boldsymbol{\theta}_{\mathrm{glob}}, \mathbf{p}_c$", fontsize=7.5,
            color=B_BLUE, ha="left")

    # Global Server Box
    server_box = patches.FancyBboxPatch((11.6, 1.05), 3.9, 1.15, boxstyle="round,pad=0.08",
                                        facecolor="#FCF3CF", edgecolor="#B7950B", linewidth=1.2)
    ax.add_patch(server_box)
    ax.text(13.55, 1.95, "Global Aggregation Server", fontsize=9.5, fontweight="bold",
            color="#7D6608", ha="center")
    ax.text(13.55, 1.6, r"$\bullet$ FedAvg / FedNova Aggregation ($R=50$ rounds/task)",
            fontsize=8, color="#555555", ha="center")
    ax.text(13.55, 1.25, r"$\bullet$ Global Prototype Estimation: $\mathbf{p}_c = \frac{1}{|\mathcal{K}_c|}\sum_k \mathbf{p}_c^{(k)}$",
            fontsize=7.8, color="#7D6608", ha="center")

    plt.tight_layout()

    # Save to both Paper/figures and report/figures
    paper_fig_path = "Paper/figures/fig1_architecture.pdf"
    paper_png_path = "Paper/figures/fig1_architecture.png"
    report_fig_path = "report/figures/fig1_architecture.pdf"
    report_png_path = "report/figures/fig1_architecture.png"

    os.makedirs("Paper/figures", exist_ok=True)
    os.makedirs("report/figures", exist_ok=True)

    fig.savefig(paper_fig_path, bbox_inches="tight", dpi=300)
    fig.savefig(paper_png_path, bbox_inches="tight", dpi=300)
    fig.savefig(report_fig_path, bbox_inches="tight", dpi=300)
    fig.savefig(report_png_path, bbox_inches="tight", dpi=300)
    plt.close(fig)

    print(f"Successfully generated new clean architecture diagram:")
    print(f"  -> {paper_fig_path}")
    print(f"  -> {paper_png_path}")

if __name__ == "__main__":
    draw_architecture_diagram()
