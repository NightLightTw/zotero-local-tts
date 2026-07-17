# Security policy

## Supported versions

Security fixes are currently provided only for the latest commit on `main`.
The prototype is version-gated to Zotero 9.0.x.

## Reporting a vulnerability

Please use GitHub's private vulnerability reporting for issues such as:

- authentication or Host/Origin validation bypasses;
- access from outside the loopback interface;
- bearer-token, paper-text, or generated-audio disclosure;
- arbitrary model or local-file access;
- unsafe Zotero method restoration or plugin lifecycle behavior.

Do not include private papers, bearer tokens, model credentials, or generated
audio containing sensitive material in a public issue. If private reporting is
temporarily unavailable, open a public issue containing no exploit details and
ask the maintainer to establish a private channel.

This is an early prototype and does not yet have a formal response-time SLA.
