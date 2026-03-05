import unittest

from src.emmanouel.state import EmmanouelState


class StateTests(unittest.TestCase):
    def test_citizen_registration_emits_credential_and_wallet_event(self):
        state = EmmanouelState()
        result = state.register_citizen("Maria Doe", "123456789", "maria@example.com")
        self.assertEqual(result["citizen"]["status"], "active")
        self.assertEqual(result["credential"]["type"], "CitizenIdentityCredential")
        wallet = state.wallet_view(result["citizen"]["holder_id"])
        self.assertEqual(len(wallet["credentials"]), 1)
        self.assertGreaterEqual(len(wallet["actions"]), 1)

    def test_policy_publication_notifies_active_citizens(self):
        state = EmmanouelState()
        state.register_citizen("A", "1", "a@a")
        state.register_citizen("B", "2", "b@b")
        policy = state.publish_policy("Open Data", "Data for all", "...")
        self.assertEqual(policy["votes"]["yes"], 0)
        for citizen in state.citizens.values():
            actions = state.wallet_view(citizen["holder_id"])["actions"]
            self.assertTrue(any(a["type"] == "new-policy" for a in actions))


if __name__ == "__main__":
    unittest.main()
