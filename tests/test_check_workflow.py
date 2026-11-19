"""Exercise the workflow evidence command against task card and config fixtures."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


CHECKER = (
    Path(__file__).resolve().parents[1] / "skills/mydevfactory/scripts/check_workflow.py"
)
ROLES = ("analyst", "backend", "frontend", "reviewer", "securitycode", "qa")
REVISION = "candidate-1"
TABLE = """## Workflow evidence

| Role | Agent | Result | Revision | Evidence |
| --- | --- | --- | --- | --- |
"""


class WorkflowEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.config = {"agents": {role: {"name": f"{role}-agent"} for role in ROLES}}
        self.rows = {
            role: f"| {role} | {role}-agent | PASS | {REVISION} | checked |"
            for role in ROLES
        }

    def run_gate(self, raw_config=None):
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            config = temp / ".mydevfactory.json"
            card = temp / "task.md"
            config.write_text(
                json.dumps(self.config) if raw_config is None else raw_config, encoding="utf-8"
            )
            card.write_text(TABLE + "\n".join(self.rows.values()) + "\n", encoding="utf-8")
            return subprocess.run(
                [
                    sys.executable, str(CHECKER), "--config", str(config),
                    "--card", str(card), "--revision", REVISION,
                ],
                capture_output=True, text=True, encoding="utf-8", check=False,
            )

    def assert_blocked(self, message, raw_config=None):
        result = self.run_gate(raw_config)
        self.assertEqual(result.returncode, 1, result)
        self.assertIn(message, result.stderr)

    def test_complete_evidence_passes_with_markdown_escaped_pipe(self):
        self.rows["backend"] = self.rows["backend"].replace(
            "checked", r"checked tests \| exit 0"
        )
        self.rows["frontend"] = self.rows["frontend"].replace("PASS", "NOT APPLICABLE")
        self.rows["frontend"] = self.rows["frontend"].replace("checked", "no UI changes")
        result = self.run_gate()
        self.assertEqual(result.returncode, 0, result)
        self.assertIn("6 configured role(s)", result.stdout)

    def test_missing_and_empty_roles_can_skip(self):
        del self.config["agents"]["analyst"]
        del self.rows["analyst"]
        self.config["agents"]["backend"] = {"name": "  "}
        self.rows["backend"] = "| backend | — | SKIPPED | — | not configured |"
        self.config["agents"]["frontend"] = {}
        del self.rows["frontend"]
        self.config["agents"]["reviewer"] = None
        del self.rows["reviewer"]
        result = self.run_gate()
        self.assertEqual(result.returncode, 0, result)
        self.assertIn("2 configured role(s)", result.stdout)

    def test_configured_role_cannot_skip(self):
        self.rows["securitycode"] = self.rows["securitycode"].replace("PASS", "SKIPPED")
        self.assert_blocked("securitycode requires a passing result")

    def test_missing_security_evidence_blocks(self):
        del self.rows["securitycode"]
        self.assert_blocked("missing configured role evidence: securitycode")

    def test_failed_security_evidence_blocks(self):
        self.rows["securitycode"] = self.rows["securitycode"].replace("PASS", "FAIL")
        self.assert_blocked("securitycode requires a passing result")

    def test_stale_evidence_blocks(self):
        self.rows["reviewer"] = self.rows["reviewer"].replace(REVISION, "candidate-0")
        self.assert_blocked("reviewer evidence is for a different revision")

    def test_qa_before_security_blocks(self):
        self.rows["securitycode"] = self.rows.pop("securitycode")
        self.assert_blocked("configured roles must run in order")

    def test_duplicate_role_evidence_blocks(self):
        self.rows["duplicate"] = self.rows["securitycode"]
        self.assert_blocked("duplicate workflow evidence for securitycode")

    def test_agent_substitution_blocks(self):
        self.rows["securitycode"] = self.rows["securitycode"].replace(
            "securitycode-agent", "reviewer-agent"
        )
        self.assert_blocked("securitycode must record configured agent securitycode-agent")

    def test_empty_evidence_blocks(self):
        self.rows["qa"] = self.rows["qa"].replace("checked", "")
        self.assert_blocked("qa requires evidence")

    def test_malformed_config_is_not_an_opt_out(self):
        for raw, message in (
            ('{"agents": []}', "agents object"),
            ('{"agents": {"securitycode": []}}', "agents.securitycode must be an object"),
            ('{"agents": {"securitycode": {"name": false}}}', "name must be a string"),
            ('{"agents": {"securitycode": null, "securitycode": null}}', "duplicate JSON key"),
        ):
            with self.subTest(raw=raw):
                self.assert_blocked(message, raw)


if __name__ == "__main__":
    unittest.main()
