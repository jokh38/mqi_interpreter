import numpy as np
from scipy.interpolate import PchipInterpolator
import math # For math.exp if preferred, though np.exp is fine for single values too

# 1. Correction Data Constants
PROTON_PER_DOSE_ENERGY_RANGE = np.array([
    70, 80, 90, 100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200, 210, 220, 230
], dtype=np.float32)

PROTON_PER_DOSE_CORRECTION_FACTORS = np.array([
    1.0, 1.12573609032495, 1.25147616113001, 1.36888442326936, 1.48668286253201,
    1.60497205195899, 1.71741194754422, 1.82898327045955, 1.94071715123743,
    2.04829230739643, 2.16168786761159, 2.27629228444253, 2.39246901674031,
    2.50561983301185, 2.63593473689952, 2.75663921459094, 2.89392497566575
], dtype=np.float32)

DOSE_PER_MU_COUNT_ENERGY_RANGE = np.array([
    70, 80, 90, 100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200, 210, 220, 230
], dtype=np.float32) # Same as PROTON_PER_DOSE_ENERGY_RANGE

DOSE_PER_MU_COUNT_CORRECTION_FACTORS = np.array([
    1.0, 0.989255716854649, 0.973421729297953, 0.967281770613755, 0.958215625815887,
    0.946937840980162, 0.942685675037711, 0.940168906626851, 0.931161417057087,
    0.918762676945622, 0.904569498824145, 0.888164591949398, 0.876689052268837,
    0.872826195199581, 0.871540965585644, 0.859481169160383, 0.8524232713089
], dtype=np.float32)

# 2. Wrapper for PCHIP Interpolator to provide constant extrapolation
class ConstExtrapPchipInterpolator:
    def __init__(self, x, y):
        if not (isinstance(x, np.ndarray) and isinstance(y, np.ndarray)):
            x = np.asarray(x, dtype=np.float32)
            y = np.asarray(y, dtype=np.float32)
        
        if x.size == 0 or y.size == 0:
            raise ValueError("Input arrays x and y must not be empty.")
        if x.size != y.size:
            raise ValueError("Input arrays x and y must have the same size.")

        # Sort by x to ensure correct behavior for PchipInterpolator and boundary conditions
        sort_indices = np.argsort(x)
        self._x = x[sort_indices]
        self._y = y[sort_indices]
        
        self._interpolator = PchipInterpolator(self._x, self._y, extrapolate=False) # extrapolate=False is default but explicit
        self._min_x = self._x[0]
        self._max_x = self._x[-1]
        self._min_y = self._y[0]
        self._max_y = self._y[-1]

    def __call__(self, xi):
        xi = np.asarray(xi) # Ensure xi is an array for vectorized operations
        # Create an output array with the same shape as xi, filled with NaNs or zeros
        yi = np.empty_like(xi, dtype=np.float32)

        # Handle values within the interpolation range
        within_range_mask = (xi >= self._min_x) & (xi <= self._max_x)
        if np.any(within_range_mask):
            yi[within_range_mask] = self._interpolator(xi[within_range_mask])

        # Handle values below the minimum range (extrapolate with min_y)
        below_range_mask = xi < self._min_x
        if np.any(below_range_mask):
            yi[below_range_mask] = self._min_y
            
        # Handle values above the maximum range (extrapolate with max_y)
        above_range_mask = xi > self._max_x
        if np.any(above_range_mask):
            yi[above_range_mask] = self._max_y
            
        # If xi was a scalar, return a scalar
        if xi.ndim == 0:
            return yi.item()
        return yi

# Create PCHIP Interpolator Instances (module level) using the wrapper
try:
    PROTON_DOSE_INTERPOLATOR = ConstExtrapPchipInterpolator(
        PROTON_PER_DOSE_ENERGY_RANGE,
        PROTON_PER_DOSE_CORRECTION_FACTORS
    )

    MU_COUNT_DOSE_INTERPOLATOR = ConstExtrapPchipInterpolator(
        DOSE_PER_MU_COUNT_ENERGY_RANGE,
        DOSE_PER_MU_COUNT_CORRECTION_FACTORS
    )
except Exception as e:
    print(f"Error creating ConstExtrapPchipInterpolators: {e}")
    PROTON_DOSE_INTERPOLATOR = None
    MU_COUNT_DOSE_INTERPOLATOR = None


# 3. Implement gaussian_energy_spread function
def gaussian_energy_spread(energy: float) -> float:
    """
    Calculates the Gaussian energy spread based on the input energy.

    Formula: 0.7224 * exp(-(((energy - 82.75) / 168.5)^2))

    Args:
        energy: The input energy value (float).

    Returns:
        The calculated Gaussian energy spread (float).
    """
    term = (energy - 82.75) / 168.5
    return 0.7224 * np.exp(-(term**2))

# 4. Placeholder for 2D bicubic interpolation
# Future implementation for 2D bicubic interpolation (e.g., for TOPAS parameters)
# from scipy.interpolate import RectBivariateSpline
# class BicubicInterpolator:
#     def __init__(self, x_coords, y_coords, z_values):
#         # self.interpolator = RectBivariateSpline(x_coords, y_coords, z_values, kx=3, ky=3)
#         pass
#
#     def __call__(self, x, y):
#         # return self.interpolator.ev(x, y)
#         pass

if __name__ == '__main__':
    print("--- Testing MQI Interpolation Logic ---")

    # Test gaussian_energy_spread
    print("\n--- Testing gaussian_energy_spread ---")
    energies_to_test_ges = [70.0, 82.75, 150.0, 230.0]
    for en in energies_to_test_ges:
        spread = gaussian_energy_spread(en)
        print(f"Gaussian energy spread for {en:.2f} MeV: {spread:.6f}")
    
    assert np.isclose(gaussian_energy_spread(82.75), 0.7224), \
        f"GES at 82.75 MeV should be 0.7224, got {gaussian_energy_spread(82.75)}"

    # Test PCHIP Interpolators (now wrapped for constant extrapolation)
    print("\n--- Testing Wrapped PCHIP Interpolators ---")
    if PROTON_DOSE_INTERPOLATOR is not None and MU_COUNT_DOSE_INTERPOLATOR is not None:
        energies_to_test_interp = [70.0, 75.0, 100.0, 155.5, 230.0]
        
        print("\nTesting PROTON_DOSE_INTERPOLATOR:")
        for en in energies_to_test_interp:
            factor = PROTON_DOSE_INTERPOLATOR(en)
            print(f"Proton/Dose factor for {en:.2f} MeV: {factor:.6f}")
        assert np.isclose(PROTON_DOSE_INTERPOLATOR(70.0), PROTON_PER_DOSE_CORRECTION_FACTORS[0])
        assert np.isclose(PROTON_DOSE_INTERPOLATOR(100.0), PROTON_PER_DOSE_CORRECTION_FACTORS[3])


        print("\nTesting MU_COUNT_DOSE_INTERPOLATOR:")
        for en in energies_to_test_interp:
            factor = MU_COUNT_DOSE_INTERPOLATOR(en)
            print(f"MUCount/Dose factor for {en:.2f} MeV: {factor:.6f}")
        assert np.isclose(MU_COUNT_DOSE_INTERPOLATOR(70.0), DOSE_PER_MU_COUNT_CORRECTION_FACTORS[0])
        assert np.isclose(MU_COUNT_DOSE_INTERPOLATOR(100.0), DOSE_PER_MU_COUNT_CORRECTION_FACTORS[3])
        
        print("\nTesting extrapolation (should be constant now):")
        extrap_low_energy = 60.0
        extrap_high_energy = 240.0
        
        # Test PROTON_DOSE_INTERPOLATOR extrapolation
        pdi_low_extrap = PROTON_DOSE_INTERPOLATOR(extrap_low_energy)
        print(f"Proton/Dose factor for {extrap_low_energy:.2f} MeV (extrapolated): {pdi_low_extrap:.6f} (should be {PROTON_PER_DOSE_CORRECTION_FACTORS[0]:.6f})")
        assert np.isclose(pdi_low_extrap, PROTON_PER_DOSE_CORRECTION_FACTORS[0])
        
        pdi_high_extrap = PROTON_DOSE_INTERPOLATOR(extrap_high_energy)
        print(f"Proton/Dose factor for {extrap_high_energy:.2f} MeV (extrapolated): {pdi_high_extrap:.6f} (should be {PROTON_PER_DOSE_CORRECTION_FACTORS[-1]:.6f})")
        assert np.isclose(pdi_high_extrap, PROTON_PER_DOSE_CORRECTION_FACTORS[-1])

        # Test MU_COUNT_DOSE_INTERPOLATOR extrapolation
        mdi_low_extrap = MU_COUNT_DOSE_INTERPOLATOR(extrap_low_energy)
        print(f"MUCount/Dose factor for {extrap_low_energy:.2f} MeV (extrapolated): {mdi_low_extrap:.6f} (should be {DOSE_PER_MU_COUNT_CORRECTION_FACTORS[0]:.6f})")
        assert np.isclose(mdi_low_extrap, DOSE_PER_MU_COUNT_CORRECTION_FACTORS[0])

        mdi_high_extrap = MU_COUNT_DOSE_INTERPOLATOR(extrap_high_energy)
        print(f"MUCount/Dose factor for {extrap_high_energy:.2f} MeV (extrapolated): {mdi_high_extrap:.6f} (should be {DOSE_PER_MU_COUNT_CORRECTION_FACTORS[-1]:.6f})")
        assert np.isclose(mdi_high_extrap, DOSE_PER_MU_COUNT_CORRECTION_FACTORS[-1])
        
        # Test with a single scalar value for extrapolation
        assert np.isclose(PROTON_DOSE_INTERPOLATOR(50.0), PROTON_PER_DOSE_CORRECTION_FACTORS[0])
        assert np.isclose(PROTON_DOSE_INTERPOLATOR(300.0), PROTON_PER_DOSE_CORRECTION_FACTORS[-1])


    else:
        print("Interpolators were not created successfully. Skipping tests.")

    print("\n--- End of MQI Interpolation Logic Tests ---")
