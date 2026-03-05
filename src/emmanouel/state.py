from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from itertools import count
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class EmmanouelState:
    citizens: dict[str, dict[str, Any]] = field(default_factory=dict)
    enterprises: dict[str, dict[str, Any]] = field(default_factory=dict)
    tax_registry: dict[str, dict[str, Any]] = field(default_factory=dict)
    credentials: list[dict[str, Any]] = field(default_factory=list)
    certificates: list[dict[str, Any]] = field(default_factory=list)
    policies: dict[int, dict[str, Any]] = field(default_factory=dict)
    wallet_actions: dict[str, list[dict[str, Any]]] = field(default_factory=dict)

    _citizen_counter: count = field(default_factory=lambda: count(1), init=False)
    _enterprise_counter: count = field(default_factory=lambda: count(1), init=False)
    _credential_counter: count = field(default_factory=lambda: count(1), init=False)
    _certificate_counter: count = field(default_factory=lambda: count(1), init=False)
    _policy_counter: count = field(default_factory=lambda: count(1), init=False)

    def _emit_wallet_action(self, holder_id: str, action_type: str, message: str, payload: dict[str, Any]) -> None:
        self.wallet_actions.setdefault(holder_id, []).append(
            {
                "type": action_type,
                "message": message,
                "payload": payload,
                "created_at": utc_now(),
            }
        )

    def register_citizen(self, full_name: str, tax_id: str, email: str) -> dict[str, Any]:
        citizen_id = f"CIT-{next(self._citizen_counter):05d}"
        holder_id = f"wallet:{citizen_id}"
        citizen = {
            "id": citizen_id,
            "holder_id": holder_id,
            "full_name": full_name,
            "tax_id": tax_id,
            "email": email,
            "status": "active",
            "registered_at": utc_now(),
        }
        self.citizens[citizen_id] = citizen
        self.tax_registry[tax_id] = {
            "owner_type": "citizen",
            "owner_id": citizen_id,
            "status": "active",
            "updated_at": utc_now(),
        }
        credential = self._issue_credential(holder_id, "CitizenIdentityCredential", {
            "citizen_id": citizen_id,
            "full_name": full_name,
            "tax_id": tax_id,
        })
        self._emit_wallet_action(
            holder_id,
            "registration-approved",
            "Η αίτηση εγγραφής πολίτη εγκρίθηκε αυτόματα από το Back-Office.",
            {"citizen_id": citizen_id, "credential_id": credential["id"]},
        )
        return {"citizen": citizen, "credential": credential}

    def register_enterprise(self, legal_name: str, tax_id: str, representative_holder_id: str) -> dict[str, Any]:
        enterprise_id = f"ENT-{next(self._enterprise_counter):05d}"
        enterprise = {
            "id": enterprise_id,
            "legal_name": legal_name,
            "tax_id": tax_id,
            "status": "active",
            "representative_holder_id": representative_holder_id,
            "registered_at": utc_now(),
        }
        self.enterprises[enterprise_id] = enterprise
        self.tax_registry[tax_id] = {
            "owner_type": "enterprise",
            "owner_id": enterprise_id,
            "status": "active",
            "updated_at": utc_now(),
        }
        credential = self._issue_credential(representative_holder_id, "EnterpriseRegistrationCredential", {
            "enterprise_id": enterprise_id,
            "legal_name": legal_name,
            "tax_id": tax_id,
        })
        self._emit_wallet_action(
            representative_holder_id,
            "enterprise-approved",
            "Η αίτηση εγγραφής επιχείρησης εγκρίθηκε αυτόματα από το Back-Office.",
            {"enterprise_id": enterprise_id, "credential_id": credential["id"]},
        )
        return {"enterprise": enterprise, "credential": credential}

    def mark_citizen_deceased(self, citizen_id: str, requested_by: str, relation: str) -> dict[str, Any]:
        citizen = self.citizens.get(citizen_id)
        if not citizen:
            raise KeyError("citizen_not_found")
        citizen["status"] = "deceased"
        citizen["deceased_at"] = utc_now()
        citizen["deceased_requested_by"] = {"name": requested_by, "relation": relation}
        self.tax_registry[citizen["tax_id"]]["status"] = "deceased"
        self.tax_registry[citizen["tax_id"]]["updated_at"] = utc_now()
        self._emit_wallet_action(
            citizen["holder_id"],
            "registry-update",
            "Ενημερώθηκε το μητρώο πολιτών μετά από αίτημα συγγενούς.",
            {"citizen_id": citizen_id, "status": "deceased"},
        )
        return citizen

    def issue_certificate(self, holder_id: str, certificate_type: str, data: dict[str, Any]) -> dict[str, Any]:
        certificate = {
            "id": f"CERT-{next(self._certificate_counter):05d}",
            "holder_id": holder_id,
            "type": certificate_type,
            "issuer": "Emmanouel State Issuer",
            "signed": True,
            "data": data,
            "issued_at": utc_now(),
        }
        self.certificates.append(certificate)
        self._emit_wallet_action(
            holder_id,
            "certificate-issued",
            f"Εκδόθηκε νέο πιστοποιητικό τύπου {certificate_type}.",
            {"certificate_id": certificate["id"]},
        )
        return certificate

    def publish_policy(self, title: str, summary: str, details: str) -> dict[str, Any]:
        policy_id = next(self._policy_counter)
        policy = {
            "id": policy_id,
            "title": title,
            "summary": summary,
            "details": details,
            "status": "discussion",
            "votes": {"yes": 0, "no": 0},
            "comments": [],
            "published_at": utc_now(),
        }
        self.policies[policy_id] = policy
        for citizen in self.citizens.values():
            if citizen["status"] == "active":
                self._emit_wallet_action(
                    citizen["holder_id"],
                    "new-policy",
                    f"Νέα πολιτική προς διαβούλευση: {title}",
                    {"policy_id": policy_id},
                )
        return policy

    def add_policy_comment(self, policy_id: int, author: str, text: str) -> dict[str, Any]:
        policy = self.policies.get(policy_id)
        if not policy:
            raise KeyError("policy_not_found")
        comment = {"author": author, "text": text, "created_at": utc_now()}
        policy["comments"].append(comment)
        return comment

    def vote_policy(self, policy_id: int, holder_id: str, vote: str) -> dict[str, Any]:
        policy = self.policies.get(policy_id)
        if not policy:
            raise KeyError("policy_not_found")
        if vote not in ("yes", "no"):
            raise ValueError("invalid_vote")
        policy["votes"][vote] += 1
        self._emit_wallet_action(
            holder_id,
            "vote-recorded",
            f"Η ψήφος σας ({vote}) για την πολιτική #{policy_id} καταγράφηκε.",
            {"policy_id": policy_id, "vote": vote},
        )
        return policy

    def wallet_view(self, holder_id: str) -> dict[str, Any]:
        credentials = [c for c in self.credentials if c["holder_id"] == holder_id]
        certificates = [c for c in self.certificates if c["holder_id"] == holder_id]
        actions = self.wallet_actions.get(holder_id, [])
        return {
            "holder_id": holder_id,
            "credentials": credentials,
            "certificates": certificates,
            "actions": actions,
            "eligible_policies": [
                {"id": p["id"], "title": p["title"], "status": p["status"]}
                for p in self.policies.values()
            ],
        }

    def dashboard_snapshot(self) -> dict[str, Any]:
        return {
            "citizen_registry": list(self.citizens.values()),
            "enterprise_registry": list(self.enterprises.values()),
            "tax_registry": self.tax_registry,
            "policies": list(self.policies.values()),
            "certificates": self.certificates,
        }

    def _issue_credential(self, holder_id: str, credential_type: str, claims: dict[str, Any]) -> dict[str, Any]:
        credential = {
            "id": f"VC-{next(self._credential_counter):06d}",
            "holder_id": holder_id,
            "type": credential_type,
            "issuer": "Emmanouel State Issuer",
            "claims": claims,
            "issued_at": utc_now(),
            "verified": True,
        }
        self.credentials.append(credential)
        return credential
