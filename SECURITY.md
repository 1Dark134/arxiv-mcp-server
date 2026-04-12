# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | Yes                |

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it responsibly.

**Do not open a public issue.** Instead, email the maintainer directly at anuj0456@gmail.com with:

- A description of the vulnerability
- Steps to reproduce the issue
- Any potential impact assessment

You can expect an initial response within 72 hours. If the vulnerability is accepted, a fix will be prioritized and a new release issued as soon as practical. If declined, you will receive an explanation.

## Security Practices

- This server makes outbound HTTP requests only to `export.arxiv.org`. No other external endpoints are contacted.
- No authentication credentials or API keys are required or stored.
- User-supplied search queries are URL-encoded before being passed to the arXiv API.
- XML responses from arXiv are parsed using Python's standard `xml.etree.ElementTree` module.
