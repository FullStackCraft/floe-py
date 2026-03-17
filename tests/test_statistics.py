"""Tests for floe.statistics."""

import math

from floe.statistics import cumulative_normal_distribution, normal_pdf


def test_cdf_at_zero():
    assert abs(cumulative_normal_distribution(0.0) - 0.5) < 1e-6


def test_cdf_positive():
    assert abs(cumulative_normal_distribution(1.0) - 0.8413) < 1e-3


def test_cdf_negative():
    assert abs(cumulative_normal_distribution(-1.0) - 0.1587) < 1e-3


def test_cdf_two_sigma():
    assert abs(cumulative_normal_distribution(2.0) - 0.9772) < 1e-3
    assert abs(cumulative_normal_distribution(-2.0) - 0.0228) < 1e-3


def test_cdf_extreme():
    assert cumulative_normal_distribution(5.0) > 0.9999
    assert cumulative_normal_distribution(-5.0) < 0.0001


def test_pdf_at_zero():
    expected = 1.0 / math.sqrt(2.0 * math.pi)
    assert abs(normal_pdf(0.0) - expected) < 1e-6


def test_pdf_at_one():
    assert abs(normal_pdf(1.0) - 0.2420) < 1e-3


def test_pdf_symmetry():
    assert abs(normal_pdf(1.0) - normal_pdf(-1.0)) < 1e-10
