"""Concept Drift Detectors for Federated Android Malware Detection (FL-MalDrift).

Implements lightweight on-device streaming drift detectors:
- ADWIN (Adaptive Windowing)
- DDM (Drift Detection Method)
- EDDM (Early Drift Detection Method)
- HDDM (Hoeffding Drift Detection Method: HDDM-A and HDDM-W)

Reference:
    Patel et al., "FL-MalDrift: a federated learning framework for malware
    detection under local concept drift", Scientific Reports (Nature Portfolio), 2026.
"""

from abc import ABC, abstractmethod
from typing import Tuple, List, Optional
import math
import numpy as np


class BaseDriftDetector(ABC):
    """Abstract Base Class for On-Device Streaming Drift Detectors."""

    def __init__(self, name: str = "BaseDriftDetector"):
        self.name = name
        self.drift_detected: bool = False
        self.warning_detected: bool = False
        self.total_samples: int = 0
        self.raw_statistic: float = 0.0

    def reset(self) -> None:
        """Reset internal detector statistics and flags."""
        self.drift_detected = False
        self.warning_detected = False
        self.total_samples = 0
        self.raw_statistic = 0.0
        self.reset_statistics()

    @abstractmethod
    def reset_statistics(self) -> None:
        """Reset algorithm-specific state variables."""
        pass

    @abstractmethod
    def update(self, error: float) -> Tuple[bool, bool]:
        """Update detector with a single prediction error/loss.

        Args:
            error: 0.0 for correct prediction, 1.0 for misclassification (or loss value).

        Returns:
            Tuple of (drift_detected, warning_detected).
        """
        pass

    def update_batch(self, preds: np.ndarray, targets: np.ndarray) -> Tuple[bool, bool]:
        """Update detector with a batch of predictions and ground truths.

        Args:
            preds: Array of predicted labels or binary predictions.
            targets: Array of target labels.

        Returns:
            Tuple of (drift_detected, warning_detected).
        """
        preds = np.asarray(preds)
        targets = np.asarray(targets)
        errors = (preds != targets).astype(np.float64)

        drift = False
        warning = False
        for err in errors:
            d, w = self.update(float(err))
            drift = drift or d
            warning = warning or w
        return drift, warning

    def get_statistic(self) -> float:
        """Return the raw detector-specific statistic (z_{c,t})."""
        return float(self.raw_statistic)

    def get_state(self) -> str:
        """Return symbolic state: 'drift', 'warning', or 'stable'."""
        if self.drift_detected:
            return "drift"
        elif self.warning_detected:
            return "warning"
        return "stable"


class ADWINDetector(BaseDriftDetector):
    """Adaptive Windowing (ADWIN) Drift Detector.

    Monitors a dynamic sliding window of error rates and splits it into two
    sub-windows W1 and W2. Drift is detected when the difference between their
    means |mu_1 - mu_2| exceeds a Hoeffding-derived bound:
        z_{c,t}^{ADWIN} = |mu_1 - mu_2|
        drift if |mu_1 - mu_2| > epsilon_cut
    """

    def __init__(self, delta: float = 0.002, max_window_size: int = 2000, min_subwindow_size: int = 5):
        super().__init__(name="ADWIN")
        self.delta = delta
        self.max_window_size = max_window_size
        self.min_subwindow_size = min_subwindow_size
        self.window: List[float] = []
        self.reset()

    def reset_statistics(self) -> None:
        self.window = []

    def update(self, error: float) -> Tuple[bool, bool]:
        self.total_samples += 1
        self.window.append(float(error))
        if len(self.window) > self.max_window_size:
            self.window.pop(0)

        n = len(self.window)
        self.drift_detected = False
        self.warning_detected = False
        max_diff = 0.0

        if n >= 2 * self.min_subwindow_size:
            step = max(1, n // 20)
            for split_idx in range(self.min_subwindow_size, n - self.min_subwindow_size + 1, step):
                w1 = self.window[:split_idx]
                w2 = self.window[split_idx:]
                n1 = len(w1)
                n2 = len(w2)
                mu1 = float(np.mean(w1))
                mu2 = float(np.mean(w2))
                diff = abs(mu1 - mu2)
                if diff > max_diff:
                    max_diff = diff

                m = 1.0 / (1.0 / n1 + 1.0 / n2)
                delta_prime = self.delta / math.log(max(2.0, float(n)))
                eps_cut = math.sqrt((1.0 / (2.0 * m)) * math.log(4.0 / max(1e-9, delta_prime)))

                if diff > 0.7 * eps_cut:
                    self.warning_detected = True

                if diff > eps_cut:
                    self.drift_detected = True
                    self.window = self.window[split_idx:]
                    break

        self.raw_statistic = max_diff
        return self.drift_detected, self.warning_detected


class DDMDetector(BaseDriftDetector):
    """Drift Detection Method (DDM).

    Monitors error rate p_i and standard deviation s_i = sqrt(p_i * (1 - p_i) / i).
    Tracks the minimum observed (p + s)_min.
        z_{c,t}^{DDM} = (p_i + s_i) - (p + s)_min
        warning if p_i + s_i >= (p + s)_min + warning_level * s_min
        drift if p_i + s_i >= (p + s)_min + drift_level * s_min
    """

    def __init__(self, min_samples: int = 30, warning_level: float = 2.0, drift_level: float = 3.0):
        super().__init__(name="DDM")
        self.min_samples = min_samples
        self.warning_level = warning_level
        self.drift_level = drift_level
        self.reset()

    def reset_statistics(self) -> None:
        self.p: float = 1.0
        self.s: float = 0.0
        self.p_min: float = float("inf")
        self.s_min: float = float("inf")
        self.ps_min: float = float("inf")
        self.sample_idx: int = 0
        self.error_count: int = 0

    def update(self, error: float) -> Tuple[bool, bool]:
        self.total_samples += 1
        self.sample_idx += 1
        if error > 0.5:
            self.error_count += 1

        self.drift_detected = False
        self.warning_detected = False

        if self.sample_idx >= self.min_samples:
            self.p = self.error_count / float(self.sample_idx)
            self.s = math.sqrt(max(0.0, self.p * (1.0 - self.p) / float(self.sample_idx)))
            ps = self.p + self.s

            if ps < self.ps_min:
                self.p_min = self.p
                self.s_min = self.s
                self.ps_min = ps

            diff = max(0.0, ps - self.ps_min)
            self.raw_statistic = diff

            drift_thresh = self.ps_min + self.drift_level * max(1e-5, self.s_min)
            warn_thresh = self.ps_min + self.warning_level * max(1e-5, self.s_min)

            if ps >= drift_thresh:
                self.drift_detected = True
                self.reset_statistics()
            elif ps >= warn_thresh:
                self.warning_detected = True
        else:
            self.raw_statistic = 0.0

        return self.drift_detected, self.warning_detected


class EDDMDetector(BaseDriftDetector):
    """Early Drift Detection Method (EDDM).

    Focuses on the average distance d_i between consecutive classification errors
    and its standard deviation s_d. Tracks maximum distance bound (d + s_d)_max:
        z_{c,t}^{EDDM} = 1 - (d_i + s_d) / (d + s_d)_max
        warning if (d_i + s_d) / (d + s_d)_max < warning_threshold (0.95)
        drift if (d_i + s_d) / (d + s_d)_max < drift_threshold (0.90)
    """

    def __init__(self, min_errors: int = 30, warning_threshold: float = 0.95, drift_threshold: float = 0.90):
        super().__init__(name="EDDM")
        self.min_errors = min_errors
        self.warning_threshold = warning_threshold
        self.drift_threshold = drift_threshold
        self.reset()

    def reset_statistics(self) -> None:
        self.num_errors: int = 0
        self.last_error_sample: int = 0
        self.distances: List[float] = []
        self.d_mean: float = 0.0
        self.d_std: float = 0.0
        self.max_ps: float = 0.0

    def update(self, error: float) -> Tuple[bool, bool]:
        self.total_samples += 1
        self.drift_detected = False
        self.warning_detected = False

        if error > 0.5:
            self.num_errors += 1
            dist = float(self.total_samples - self.last_error_sample)
            self.last_error_sample = self.total_samples
            self.distances.append(dist)

            if len(self.distances) > 200:
                self.distances.pop(0)

            if self.num_errors >= self.min_errors:
                self.d_mean = float(np.mean(self.distances))
                self.d_std = float(np.std(self.distances))
                curr_ps = self.d_mean + 2.0 * self.d_std

                if curr_ps > self.max_ps:
                    self.max_ps = curr_ps

                if self.max_ps > 1e-6:
                    ratio = curr_ps / self.max_ps
                    self.raw_statistic = max(0.0, 1.0 - ratio)

                    if ratio < self.drift_threshold:
                        self.drift_detected = True
                        self.reset_statistics()
                    elif ratio < self.warning_threshold:
                        self.warning_detected = True
                else:
                    self.raw_statistic = 0.0

        return self.drift_detected, self.warning_detected


class HDDMDetector(BaseDriftDetector):
    """Hoeffding Drift Detection Method (HDDM).

    Uses Hoeffding's inequality to monitor shifts in error rate:
        z_{c,t}^{HDDM} = |mu_t - mu_0|
        drift if |mu_t - mu_0| > epsilon

    Variants:
        - 'HDDM_A': Arithmetic moving average
        - 'HDDM_W': Exponentially Weighted Moving Average (EWMA, default in FL-MalDrift)
    """

    def __init__(
        self,
        variant: str = "HDDM_W",
        alpha: float = 0.001,
        warning_alpha: float = 0.005,
        decay: float = 0.85,
        min_samples: int = 15,
    ):
        super().__init__(name=f"HDDM ({variant})")
        self.variant = variant.upper()
        self.alpha = alpha
        self.warning_alpha = warning_alpha
        self.decay = decay
        self.min_samples = min_samples
        self.reset()

    def reset_statistics(self) -> None:
        self.n_samples: int = 0
        self.mu_curr: float = 0.0
        self.mu_min: float = float("inf")
        self.weight_sum: float = 0.0
        self.weighted_error: float = 0.0

    def update(self, error: float) -> Tuple[bool, bool]:
        self.total_samples += 1
        self.n_samples += 1
        err = float(error)

        self.drift_detected = False
        self.warning_detected = False

        if self.variant == "HDDM_W":
            self.weighted_error = self.decay * self.weighted_error + err
            self.weight_sum = self.decay * self.weight_sum + 1.0
            self.mu_curr = self.weighted_error / max(1e-9, self.weight_sum)
        else:
            self.mu_curr += (err - self.mu_curr) / float(self.n_samples)

        if self.n_samples >= self.min_samples:
            if self.mu_curr < self.mu_min:
                self.mu_min = self.mu_curr

            diff = max(0.0, self.mu_curr - self.mu_min)
            self.raw_statistic = diff

            eff_n = float(self.n_samples)
            eps_drift = math.sqrt(math.log(1.0 / max(1e-12, self.alpha)) / (2.0 * eff_n))
            eps_warning = math.sqrt(math.log(1.0 / max(1e-12, self.warning_alpha)) / (2.0 * eff_n))

            if diff > eps_drift:
                self.drift_detected = True
                self.reset_statistics()
            elif diff > eps_warning:
                self.warning_detected = True
        else:
            self.raw_statistic = 0.0

        return self.drift_detected, self.warning_detected


def build_drift_detector(detector_type: str = "hddm_w", **kwargs) -> BaseDriftDetector:
    """Factory function to instantiate specified drift detector.

    Args:
        detector_type: One of ('hddm_w', 'hddm_a', 'adwin', 'ddm', 'eddm').
        **kwargs: Optional hyperparameter overrides.

    Returns:
        Instance of BaseDriftDetector.
    """
    dtype = detector_type.lower()
    if dtype in ("hddm_w", "hddm-w", "hddm"):
        return HDDMDetector(variant="HDDM_W", **kwargs)
    elif dtype in ("hddm_a", "hddm-a"):
        return HDDMDetector(variant="HDDM_A", **kwargs)
    elif dtype == "adwin":
        return ADWINDetector(**kwargs)
    elif dtype == "ddm":
        return DDMDetector(**kwargs)
    elif dtype == "eddm":
        return EDDMDetector(**kwargs)
    else:
        raise ValueError(
            f"Unsupported drift detector '{detector_type}'. Supported: "
            f"['hddm_w', 'hddm_a', 'adwin', 'ddm', 'eddm']"
        )
