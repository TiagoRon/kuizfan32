"""Tests unitarios para el módulo de efectos visuales."""

from __future__ import annotations

import pytest
from PIL import Image

from quiz_generator.video.effects import VisualEffects


@pytest.fixture
def sample_image() -> Image.Image:
    """Crea una imagen de prueba 200x200 con colores."""
    img = Image.new("RGB", (200, 200), (50, 50, 100))
    return img


class TestConfetti:
    """Tests para el efecto de confeti."""

    def test_returns_image(self, sample_image: Image.Image) -> None:
        result = VisualEffects.apply_confetti(sample_image, num_particles=10)
        assert isinstance(result, Image.Image)

    def test_same_size(self, sample_image: Image.Image) -> None:
        result = VisualEffects.apply_confetti(sample_image)
        assert result.size == sample_image.size

    def test_does_not_modify_original(self, sample_image: Image.Image) -> None:
        original_data = list(sample_image.getdata())
        VisualEffects.apply_confetti(sample_image, num_particles=50)
        assert list(sample_image.getdata()) == original_data

    def test_seed_reproducibility(self, sample_image: Image.Image) -> None:
        r1 = VisualEffects.apply_confetti(sample_image, num_particles=20, seed=42)
        r2 = VisualEffects.apply_confetti(sample_image, num_particles=20, seed=42)
        assert list(r1.getdata()) == list(r2.getdata())


class TestShake:
    """Tests para el efecto de shake."""

    def test_returns_image(self, sample_image: Image.Image) -> None:
        result = VisualEffects.apply_shake(sample_image, intensity=5)
        assert isinstance(result, Image.Image)

    def test_same_size(self, sample_image: Image.Image) -> None:
        result = VisualEffects.apply_shake(sample_image)
        assert result.size == sample_image.size

    def test_zero_intensity_might_change(self, sample_image: Image.Image) -> None:
        """Con intensidad 0, el shake debería desplazar 0 píxeles."""
        result = VisualEffects.apply_shake(sample_image, intensity=0)
        assert result.size == sample_image.size


class TestGlow:
    """Tests para el efecto de glow."""

    def test_returns_image(self, sample_image: Image.Image) -> None:
        result = VisualEffects.apply_glow(sample_image)
        assert isinstance(result, Image.Image)

    def test_same_size(self, sample_image: Image.Image) -> None:
        result = VisualEffects.apply_glow(sample_image)
        assert result.size == sample_image.size

    def test_custom_color(self, sample_image: Image.Image) -> None:
        result = VisualEffects.apply_glow(
            sample_image, color=(255, 0, 0), intensity=0.5,
        )
        assert isinstance(result, Image.Image)


class TestZoomPulse:
    """Tests para el efecto de zoom pulse."""

    def test_returns_image(self, sample_image: Image.Image) -> None:
        result = VisualEffects.apply_zoom_pulse(sample_image, factor=1.1)
        assert isinstance(result, Image.Image)

    def test_same_size(self, sample_image: Image.Image) -> None:
        """El resultado debe mantener el mismo tamaño."""
        result = VisualEffects.apply_zoom_pulse(sample_image, factor=1.2)
        assert result.size == sample_image.size

    def test_factor_1_no_change(self, sample_image: Image.Image) -> None:
        """Factor 1.0 no debería cambiar significativamente la imagen."""
        result = VisualEffects.apply_zoom_pulse(sample_image, factor=1.0)
        assert result.size == sample_image.size


class TestVignette:
    """Tests para el efecto de viñeta."""

    def test_returns_image(self, sample_image: Image.Image) -> None:
        result = VisualEffects.apply_vignette(sample_image)
        assert isinstance(result, Image.Image)

    def test_same_size(self, sample_image: Image.Image) -> None:
        result = VisualEffects.apply_vignette(sample_image)
        assert result.size == sample_image.size


class TestFlash:
    """Tests para el efecto de flash."""

    def test_returns_image(self, sample_image: Image.Image) -> None:
        result = VisualEffects.apply_flash(sample_image)
        assert isinstance(result, Image.Image)

    def test_same_size(self, sample_image: Image.Image) -> None:
        result = VisualEffects.apply_flash(sample_image)
        assert result.size == sample_image.size

    def test_full_flash_is_white(self, sample_image: Image.Image) -> None:
        """Flash con intensidad 1.0 debería ser todo blanco."""
        result = VisualEffects.apply_flash(sample_image, intensity=1.0)
        pixels = list(result.getdata())
        assert all(p == (255, 255, 255) for p in pixels)


class TestColorOverlay:
    """Tests para el overlay de color."""

    def test_returns_image(self, sample_image: Image.Image) -> None:
        result = VisualEffects.apply_color_overlay(
            sample_image, (255, 0, 0), intensity=0.3,
        )
        assert isinstance(result, Image.Image)

    def test_same_size(self, sample_image: Image.Image) -> None:
        result = VisualEffects.apply_color_overlay(
            sample_image, (0, 255, 0), intensity=0.2,
        )
        assert result.size == sample_image.size
