"""The repo's first tests (2026-08-05).

Stdlib ``unittest``, not pytest — the env is pinned deliberately and pytest is not in it.
Run from the repo root::

    PYTHONPATH=$PWD micromamba/envs/sfincs/bin/python -m unittest discover -s tests -v

These cover the invariants that, when they broke, cost real work:

* the domain registry and its fingerprints agreeing with each other,
* ``exp_root``/``sealed_template`` actually being per-domain,
* brackets staying OUT of ``EXPECTED``,
* and above all, ``prepare_experiment`` refusing a wrong domain BEFORE it destroys the
  destination directory.

Nothing here runs SFINCS, reads a run output, or writes into ``experiments/``.
"""

from __future__ import annotations

import os
import unittest
from pathlib import Path

from nj_sfincs import domain, premier
from nj_sfincs.config import ROOT, exp_root


class _DomainEnv(unittest.TestCase):
    """Base that restores NJ_DOMAIN, which several tests set."""

    def setUp(self) -> None:
        self._saved = os.environ.get("NJ_DOMAIN")

    def tearDown(self) -> None:
        if self._saved is None:
            os.environ.pop("NJ_DOMAIN", None)
        else:
            os.environ["NJ_DOMAIN"] = self._saved


class TestDomainRegistry(_DomainEnv):
    def test_key_matches_name(self):
        for key, dom in domain.DOMAINS.items():
            self.assertEqual(key, dom.name, f"DOMAINS[{key!r}].name is {dom.name!r}")

    def test_default_domain_is_registered(self):
        self.assertIn(domain.DEFAULT_DOMAIN, domain.DOMAINS)

    def test_active_follows_env(self):
        for name in domain.DOMAINS:
            os.environ["NJ_DOMAIN"] = name
            self.assertEqual(domain.active().name, name)

    def test_active_is_read_at_call_time(self):
        """Not cached at import — the whole registry depends on this."""
        os.environ["NJ_DOMAIN"] = "v1_monmouth"
        first = domain.active().name
        os.environ["NJ_DOMAIN"] = "v2_barnegat"
        self.assertNotEqual(first, domain.active().name)

    def test_unknown_domain_raises(self):
        os.environ["NJ_DOMAIN"] = "v9_atlantis"
        with self.assertRaises(KeyError):
            domain.active()

    def test_basin_rules_are_named_and_unique(self):
        for name, dom in domain.DOMAINS.items():
            names = domain.hwm_basin_names(dom)
            self.assertTrue(names, f"{name} has no HWM basin rules")
            self.assertEqual(len(names), len(set(names)),
                             f"{name} has duplicate basin names: {names}")
            self.assertNotIn("unassigned", names,
                             "'unassigned' is the fallback bucket, not a rule name")

    def test_waterlevel_support_is_declared(self):
        """A domain with no declared support count cannot have the Cape May trap caught."""
        for name, dom in domain.DOMAINS.items():
            self.assertIsNotNone(dom.n_waterlevel_support,
                                 f"{name} does not declare n_waterlevel_support")


class TestFingerprints(_DomainEnv):
    def test_every_domain_has_a_fingerprint(self):
        self.assertEqual(set(premier.EXPECTED), set(domain.DOMAINS),
                         "a domain without a fingerprint audits UNRECOGNISED, which "
                         "reads exactly like a real domain error")

    def test_expected_resolves_per_domain(self):
        for name in domain.DOMAINS:
            os.environ["NJ_DOMAIN"] = name
            self.assertEqual(premier.expected(), premier.EXPECTED[name])

    def test_fingerprints_are_distinct(self):
        fps = list(premier.EXPECTED.values())
        self.assertEqual(len(fps), len(set(fps)), "two domains share a fingerprint")

    def test_v2_premask_differs_only_in_sha(self):
        """The mask repair moved the sha but not the cell counts.

        Documented because it is the trap: you cannot tell these two apart by faces or
        boundary edges, only by the hash.
        """
        a, b = premier.V2_BARNEGAT, premier.V2_BARNEGAT_PREMASK
        self.assertEqual(a.n_faces, b.n_faces)
        self.assertEqual(a.n_boundary_edges, b.n_boundary_edges)
        self.assertNotEqual(a.sha_z_mask, b.sha_z_mask)
        self.assertNotEqual(a, b)

    def test_brackets_are_not_in_expected(self):
        """A bracket in EXPECTED would make assert_sealed_domain PASS on it."""
        expected_fps = set(premier.EXPECTED.values())
        for name, brk in premier.BRACKETS.items():
            self.assertNotIn(brk.fingerprint, expected_fps,
                             f"bracket {name!r} is registered as a legitimate domain")

    def test_bracket_base_domain_is_registered(self):
        for name, brk in premier.BRACKETS.items():
            self.assertIn(brk.base_domain, domain.DOMAINS,
                          f"bracket {name!r} names an unknown base domain")

    def test_known_covers_every_expected_fingerprint(self):
        """KNOWN is what turns a BAD line into a diagnosis instead of 'UNRECOGNISED'."""
        for name, fp in premier.EXPECTED.items():
            self.assertIn(fp, premier.KNOWN, f"{name}'s fingerprint has no KNOWN label")


class TestExperimentPaths(_DomainEnv):
    def test_exp_root_is_domain_scoped(self):
        seen = set()
        for name in domain.DOMAINS:
            os.environ["NJ_DOMAIN"] = name
            root = exp_root()
            self.assertEqual(root.name, name)
            self.assertEqual(root.parent, ROOT / "experiments")
            seen.add(root)
        self.assertEqual(len(seen), len(domain.DOMAINS),
                         "exp_root() returned the same path for two domains — the "
                         "same arm name on two domains would collide")

    def test_sealed_template_lives_under_exp_root(self):
        for name in domain.DOMAINS:
            os.environ["NJ_DOMAIN"] = name
            self.assertEqual(premier.sealed_template().parent, exp_root())
            self.assertEqual(premier.sealed_template().name, premier.TEMPLATE_NAME)

    def test_sealed_and_legacy_templates_differ(self):
        self.assertNotEqual(premier.sealed_template(), premier.legacy_template())

    def test_frozen_mesh_declared_per_domain(self):
        self.assertEqual(set(premier.FROZEN_MESH), set(domain.DOMAINS))
        for name, rel in premier.FROZEN_MESH.items():
            self.assertTrue(rel.endswith(name),
                            f"frozen mesh for {name} is {rel!r} — the path should be "
                            "keyed on the domain so it cannot be picked by omission")


class TestStagingIsSafeBeforeItIsDestructive(_DomainEnv):
    """⭐ The regression test for 2026-08-05.

    ``prepare_experiment`` used to ``rmtree`` the destination and ``copytree`` the
    template BEFORE asserting the domain, so a wrong-domain refusal could only ever be
    reported once the destination was already gone. That destroyed
    ``experiments/v2_barnegat/faber-waves-premier``'s output — 1.8 GB of solver results —
    from a command whose author believed it was read-only.

    The fix is ordering, so this test asserts ordering: when the domain check fails, the
    destination must still be on disk, untouched.
    """

    def test_domain_is_checked_before_anything_destructive(self):
        """Assert ORDERING, not just the end state.

        ``shutil.rmtree``/``copytree`` are spied rather than allowed to run: under the
        old ordering a real ``copytree`` would clone the multi-GB template into a temp
        dir before the test could catch anything. Spying records the sequence, which is
        the property actually under test — and it fails loudly on the old code, where
        'rmtree' lands in the log before 'domain-check'.
        """
        import shutil as _shutil
        import tempfile

        import run_experiments as rx

        name = next(iter(rx.EXPERIMENTS))
        events: list[str] = []

        def refuse(*_a, **_k):
            events.append("domain-check")
            raise premier.WrongDomainError("simulated wrong domain")

        with tempfile.TemporaryDirectory() as tmp:
            fake_root = Path(tmp) / "experiments"
            victim = fake_root / name
            victim.mkdir(parents=True)
            canary = victim / "sfincs_map.nc"
            canary.write_text("precious solver output")

            saved = (rx.EXP_ROOT, premier.assert_sealed_domain,
                     premier.assert_bracket, _shutil.rmtree, _shutil.copytree)
            rx.EXP_ROOT = fake_root
            premier.assert_sealed_domain = refuse
            premier.assert_bracket = refuse
            _shutil.rmtree = lambda *a, **k: events.append("rmtree")
            _shutil.copytree = lambda *a, **k: events.append("copytree")
            try:
                with self.assertRaises(premier.WrongDomainError):
                    rx.prepare_experiment(name, object())
            finally:
                (rx.EXP_ROOT, premier.assert_sealed_domain, premier.assert_bracket,
                 _shutil.rmtree, _shutil.copytree) = saved

            self.assertEqual(events[0], "domain-check",
                             f"the domain check must come FIRST; got {events}. This is "
                             "the 2026-08-05 data-loss bug: a wrong-domain refusal that "
                             "only fires after the destination is already destroyed.")
            self.assertNotIn("rmtree", events,
                             f"nothing destructive may run after a refusal; got {events}")
            self.assertTrue(canary.exists())
            self.assertEqual(canary.read_text(), "precious solver output")

    def test_check_template_domain_touches_nothing(self):
        """The read-only path must not create EXP_ROOT as a side effect."""
        import tempfile

        import run_experiments as rx

        name = next(iter(rx.EXPERIMENTS))
        with tempfile.TemporaryDirectory() as tmp:
            fake_root = Path(tmp) / "experiments"   # deliberately absent
            saved_root, saved_assert = rx.EXP_ROOT, premier.assert_sealed_domain
            premier.assert_sealed_domain = lambda *_a, **_k: None
            premier.assert_bracket = premier.assert_bracket
            rx.EXP_ROOT = fake_root
            try:
                rx.check_template_domain(name)
            finally:
                rx.EXP_ROOT, premier.assert_sealed_domain = saved_root, saved_assert
            self.assertFalse(fake_root.exists(),
                             "check_template_domain created directories")


if __name__ == "__main__":
    unittest.main()
