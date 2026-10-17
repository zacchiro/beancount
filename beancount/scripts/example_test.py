__copyright__ = "Copyright (C) 2014, 2016-2017, 2019, 2021, 2024-2025  Martin Blais"
__license__ = "GNU GPLv2"

import datetime
import random
import unittest

import click.testing

from beancount import loader
from beancount.core import data
from beancount.core.number import D
from beancount.ops import validation
from beancount.scripts import example
from beancount.utils import test_utils


class TestScriptExample(test_utils.ClickTestCase):
    def test_generate(self):
        # For some reason rv.stdout includes stderr output when run from Bazel,
        # so you have to disable that from the program.
        rv = self.run_with_args(example.main)
        self.assertTrue(rv.stdout)

        loaded_entries, errors, _ = loader.load_string(
            rv.stdout, extra_validations=validation.HARDCORE_VALIDATIONS
        )
        self.assertFalse(errors)

    def test_generate_with_date(self):
        # For some reason rv.stdout includes stderr output when run from Bazel,
        # so you have to disable that from the program.
        rv = self.run_with_args(example.main, "--date-birth", "1988-07-01")
        self.assertTrue(rv.stdout)

        loaded_entries, errors, _ = loader.load_string(
            rv.stdout, extra_validations=validation.HARDCORE_VALIDATIONS
        )
        self.assertFalse(errors)

    def test_generate_density(self):
        args = ("--seed", "1", "--date-begin", "2024-01-01", "--date-end", "2025-01-01")
        rv_default = self.run_with_args(example.main, *args)
        rv_one = self.run_with_args(example.main, *args, "--density", "1")
        self.assertEqual(rv_default.stdout, rv_one.stdout)

        rv = self.run_with_args(example.main, *args, "--density", "5")
        entries, errors, _ = loader.load_string(
            rv.stdout, extra_validations=validation.HARDCORE_VALIDATIONS
        )
        self.assertFalse(errors)
        default_entries, _, _ = loader.load_string(rv_default.stdout)
        self.assertGreater(
            len(list(data.filter_txns(entries))),
            2 * len(list(data.filter_txns(default_entries))),
        )

    def test_generate_density_invalid(self):
        runner = click.testing.CliRunner()
        for density in "0", "-1", "1e6":
            rv = runner.invoke(example.main, ["--density", density])
            self.assertEqual(2, rv.exit_code)
            self.assertIn("Invalid value for '--density'", rv.output)


class TestExampleHelpers(unittest.TestCase):
    def test_date_random_seq_density(self):
        date_begin = datetime.date(2020, 1, 1)
        date_end = datetime.date(2021, 1, 1)
        random.seed(0)
        dates = list(example.date_random_seq(date_begin, date_end, 1, 5))
        random.seed(0)
        self.assertEqual(
            dates, list(example.date_random_seq(date_begin, date_end, 1, 5, 1.0))
        )
        dates_dense = list(example.date_random_seq(date_begin, date_end, 1, 5, 10.0))
        self.assertGreater(len(dates_dense), 8 * len(dates))
        self.assertEqual(dates_dense, sorted(dates_dense))
        self.assertTrue(all(date_begin <= date < date_end for date in dates_dense))

    def test_date_random_seq_tiny_density(self):
        date_begin = datetime.date(2020, 1, 1)
        date_end = datetime.date(2021, 1, 1)
        self.assertEqual(
            [], list(example.date_random_seq(date_begin, date_end, 1, 5, 1e-6))
        )
        self.assertEqual(
            [], list(example.date_random_seq(date_begin, date_end, 1, 5, 1e-300))
        )

    def test_random_count(self):
        random.seed(0)
        self.assertTrue(all(example.random_count(0.0, 1.0) == 0 for _ in range(100)))
        self.assertTrue(all(example.random_count(1.0, 3.0) == 3 for _ in range(100)))
        total = sum(example.random_count(0.3, 2.5) for _ in range(10000))
        self.assertAlmostEqual(0.75, total / 10000, delta=0.05)

    def test_scale_amount(self):
        self.assertEqual(D("12.34"), example.scale_amount(D("12.34"), 1))
        self.assertAlmostEqual(1.5, example.scale_amount(15.0, 10.0))
        self.assertEqual(0.01, example.scale_amount(15.0, 10000.0))
        self.assertAlmostEqual(-1.5, example.scale_amount(-15.0, 10.0))
        self.assertEqual(-0.01, example.scale_amount(-15.0, 10000.0))
        self.assertEqual(-15.0, example.scale_amount(-15.0, 1))


if __name__ == "__main__":
    unittest.main()
