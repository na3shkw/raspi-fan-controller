import pytest

from main import clamp, check_pwm_params, build_temp_duty_map, resolve_duty


def make_config(curve, frequency=None):
    return {
        "pwm": {
            "curve": curve,
            "frequency": frequency or {"default": 1, "low_clock": 1},
        }
    }


class TestClamp:
    @pytest.mark.parametrize(
        "num, expected",
        [
            pytest.param(0.5, 0.5, id="within_range"),
            pytest.param(-1, 0, id="below_minimum"),
            pytest.param(2, 1, id="above_maximum"),
        ],
    )
    def test_clamp(self, num, expected):
        assert clamp(num, 0, 1) == expected


class TestCheckPwmParams:
    def test_valid_config_does_not_raise(self):
        config = make_config([
            {"temperature": 40, "duty": 0.3},
            {"temperature": 50, "duty": 0.6},
            {"temperature": 60, "duty": 1.0},
        ])
        check_pwm_params(config)

    def test_single_point_curve_is_valid(self):
        config = make_config([{"temperature": 50, "duty": 1}])
        check_pwm_params(config)

    @pytest.mark.parametrize(
        "curve, frequency, expected_exception",
        [
            pytest.param([], None, ValueError, id="empty_curve"),
            pytest.param([{"temperature": 40}], None, ValueError, id="missing_key"),
            pytest.param([{"temperature": 40.5, "duty": 0.5}], None, TypeError, id="non_integer_temperature"),
            pytest.param([{"temperature": 40, "duty": 1.5}], None, ValueError, id="duty_out_of_range"),
            pytest.param(
                [{"temperature": 50, "duty": 0.5}, {"temperature": 40, "duty": 1.0}],
                None,
                ValueError,
                id="non_ascending_temperature",
            ),
            pytest.param(
                [{"temperature": 40, "duty": 0.5}, {"temperature": 40, "duty": 1.0}],
                None,
                ValueError,
                id="duplicate_temperature",
            ),
            pytest.param(
                [{"temperature": 40, "duty": 0.5}],
                {"default": 1},
                ValueError,
                id="missing_frequency_keys",
            ),
        ],
    )
    def test_invalid_config_raises(self, curve, frequency, expected_exception):
        config = make_config(curve, frequency=frequency)
        with pytest.raises(expected_exception):
            check_pwm_params(config)


class TestDutyResolution:
    @pytest.fixture
    def curve(self):
        return [
            {"temperature": 40, "duty": 0.3},
            {"temperature": 50, "duty": 0.6},
            {"temperature": 60, "duty": 1.0},
        ]

    @pytest.fixture
    def built_curve(self, curve):
        return build_temp_duty_map(curve)

    def test_below_lowest_point_is_clamped(self, built_curve):
        temperatures, duties, temp_duty_map = built_curve
        assert resolve_duty(20, temperatures, duties, temp_duty_map) == 0.3

    def test_above_highest_point_is_clamped(self, built_curve):
        temperatures, duties, temp_duty_map = built_curve
        assert resolve_duty(70, temperatures, duties, temp_duty_map) == 1.0

    def test_at_defined_points_matches_exactly(self, built_curve):
        temperatures, duties, temp_duty_map = built_curve
        assert resolve_duty(40, temperatures, duties, temp_duty_map) == 0.3
        assert resolve_duty(50, temperatures, duties, temp_duty_map) == 0.6
        assert resolve_duty(60, temperatures, duties, temp_duty_map) == 1.0

    def test_interpolates_between_points(self, built_curve):
        temperatures, duties, temp_duty_map = built_curve
        assert resolve_duty(45, temperatures, duties, temp_duty_map) == pytest.approx(0.45)

    def test_single_point_curve_is_always_constant(self):
        curve = [{"temperature": 50, "duty": 0.7}]
        temperatures, duties, temp_duty_map = build_temp_duty_map(curve)
        assert resolve_duty(0, temperatures, duties, temp_duty_map) == 0.7
        assert resolve_duty(50, temperatures, duties, temp_duty_map) == 0.7
        assert resolve_duty(100, temperatures, duties, temp_duty_map) == 0.7
