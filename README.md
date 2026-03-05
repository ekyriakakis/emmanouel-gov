# Emmanouel State Platform

Πρωτότυπο πλατφόρμας για το Κράτος Emmanouel με πλήρη διαλειτουργικότητα μεταξύ:

1. **Ιστότοπου πολιτών** (εγγραφές, ενημέρωση, σχόλια/συμμετοχή).
2. **Back-Office Issuer Dashboard** (αυτόματες εγκρίσεις, έκδοση VC/πιστοποιητικών, πολιτικές).
3. **Ψηφιακού πορτοφολιού** (VCs, πιστοποιητικά, ενέργειες συμμετοχής).

## Τι περιλαμβάνει

- Μητρώο πολιτών, επιχειρήσεων και φορολογικό μητρώο.
- Αυτόματη έγκριση αιτήσεων εγγραφής.
- Αυτόματη έκδοση Verifiable Credentials σε holder wallet IDs.
- Ροή θανάτου πολίτη μετά από αίτημα συγγενούς.
- Έκδοση πιστοποιητικών από το κράτος-issuer.
- Δημοσίευση πολιτικών, διαβούλευση και ψηφοφορία.
- API που συνδέει website, dashboard και wallet.

## Εκτέλεση

```bash
python -m src.emmanouel.server
```

Άνοιξε: `http://localhost:8000`

## API (ενδεικτικά)

- `POST /api/register/citizen`
- `POST /api/register/enterprise`
- `POST /api/citizen/deceased`
- `POST /api/certificates`
- `POST /api/policies`
- `POST /api/policies/{id}/comment`
- `POST /api/policies/{id}/vote`
- `GET /api/dashboard`
- `GET /api/wallet?holder_id=wallet:CIT-00001`

## Tests

```bash
python -m unittest discover -s tests
```
