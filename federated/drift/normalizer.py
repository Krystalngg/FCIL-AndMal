"""Unified Drift Score Normalizer for Federated Android Malware Detection.

Implements Z-Score transformation with sliding-window pooling and [0, 1] clipping,
along with discrete state mapping (no-alarm -> 0.0, warning -> 0.5, drift -> 1.0)
as formulated in FL-MalDrift (Patel et al., 2026).
"""

from typing import List, Optional
import numpy as np


class DriftScoreNormalizer:
    """Sliding-Window Z-Score Normalizer for Client Drift Statistics.

    Normalizes heterogeneous detector statistics z_{c,t} into bounded [0, 1]
    drift scores s_{c,t}:
        s_{c,t} = clip_{[0, 1]}( (z_{c,t} - mu_t^{(W)}) / (sigma_t^{(W)} + eps) )

    Also supports discrete symbolic mappings:
        - 'stable' / 'no-alarm' -> 0.0
        - 'warning'             -> 0.5
        - 'drift'               -> 1.0
    """

    def __init__(self, window_size: int = 10, eps: float = 1e-5, min_window_samples: int = 3):
        """Initialize the normalizer.

        Args:
            window_size: Number of past rounds (W) to retain for pooled statistics.
            eps: Numerical stability constant.
            min_window_samples: Minimum observed statistics needed before active z-score scaling.
        """
        self.window_size = window_size
        self.eps = eps
        self.min_window_samples = min_window_samples
        self.history: List[float] = []

    def reset(self) -> None:
        """Clear historical statistics."""
        self.history.clear()

    def record_statistic(self, z: float) -> None:
        """Record an observed raw detector statistic into the sliding window."""
        self.history.append(float(z))
        if len(self.history) > self.window_size * 50:  # Bound stored items
            self.history = self.history[-self.window_size * 20:]

    def get_window_stats(self) -> tuple[float, float]:
        """Compute mean and std over recent sliding window."""
        if not self.history:
            return 0.0, 1.0
        recent = self.history[-max(len(self.history), self.window_size):]
        mu = float(np.mean(recent))
        sigma = float(np.std(recent))
        return mu, sigma

    def normalize(self, z: float, state: str = "stable") -> float:
        """Convert raw statistic z and symbolic state into normalized score s in [0, 1].

        Args:
            z: Raw detector statistic z_{c,t}.
            state: Detector symbolic state ('stable', 'warning', 'drift').

        Returns:
            Normalized drift score s_{c,t} in [0.0, 1.0].
        """
        # Always record observed statistic
        self.record_statistic(z)

        # Baseline discrete score from symbolic state
        state_lower = str(state).lower()
        if state_lower == "drift":
            state_score = 1.0
        elif state_lower == "warning":
            state_score = 0.5
        else:
            state_score = 0.0

        # If not enough history, rely primarily on detector state and raw magnitude
        if len(self.history) < self.min_window_samples:
            raw_clipped = float(np.clip(z, 0.0, 1.0))
            return float(np.clip(max(state_score, raw_clipped), 0.0, 1.0))

        # Compute empirical mean and std over sliding window
        mu, sigma = self.get_window_stats()

        # Z-score normalization with bounded clipping to [0, 1]
        z_norm = (z - mu) / (sigma + self.eps)
        # Shift standard normal (0 mean, 1 std) so mean maps to ~0.5, or direct min-clip
        score = float(np.clip(0.5 + 0.25 * z_norm, 0.0, 1.0))

        # Integrate symbolic state as per paper (Patel et al. 2026, Sec. 4.1):
        #   no-alarm → 0, warning → 0.5, drift → 1.0 (exact discrete mapping)
        if state_lower == "drift":
            score = 1.0  # paper: drift → 1 (exact)
        elif state_lower == "warning":
            score = max(score, 0.5)  # paper: warning → 0.5

        return float(np.clip(score, 0.0, 1.0))
