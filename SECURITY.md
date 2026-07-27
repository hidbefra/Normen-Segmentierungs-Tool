## Sicherheitsrichtlinie

Kurz: Melde Sicherheitsprobleme vertraulich und folge den untenstehenden Schritten.

### 1) Sofortige Meldung
- Nutze die GitHub Security-Features (Security Advisories) oder eröffne ein vertrauliches Issue.
- Teile keine geheimen Zugangsdaten oder private Schlüssel in Issues/PRs.

### 2) Was melden
- Reproduzierbare Schritte, betroffene Versionen, Impact (RCE, Datenleck etc.), mögliche Fix-Vorschläge.

### 3) Kontakt & Ablauf
- Bevorzuge den vertraulichen Weg über GitHub Security; wenn nicht möglich, kontaktiere den Repo-Owner direkt.
- Wir bestätigen Empfang innerhalb von 48 Stunden und kommunizieren einen geplanten Fix-/Mitigationszeitraum.

### 4) Sofortmaßnahmen (Repo-Besitzer)
- Geheimnisse rotieren und betroffene Keys ungültig machen.
- Falls nötig: temporäre Branch-Sperren, schnellen Hotfix-Branch erstellen und CI-Checks erzwingen.

### 5) Empfehlungen für Contributors
- Keine API-Keys, Passwörter oder PII ins Repo committen.
- Nutze GitHub Secrets / Vault für sensible Daten.
- Aktiviere 2FA für alle Konten mit Merge-Rechten.

### 6) Präventive Maßnahmen (Empfohlen)
- Aktivieren: Dependabot, Secret Scanning, Code Scanning (SAST) in CI.
- Branch-Protection: erzwinge PRs, Review, erfolgreiche CI-Checks und kein Force-Push auf `main`.
- Regelmäßige Rotation von Schlüsseln und Abhängigkeiten.

### 7) Lizenz & Offenlegung
- Nach Fix wird die Sicherheitsmeldung verantwortungsvoll veröffentlicht, sofern keine rechtlichen Gründe dagegensprechen.

Vielen Dank für das Melden von Problemen — Sicherheit hat Priorität.
