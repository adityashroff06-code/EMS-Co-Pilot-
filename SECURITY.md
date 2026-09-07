# Security and credential handling

The offline CLI does not require secrets or network access. The optional AI workflow reads `OPENAI_API_KEY` from the runtime environment, and the dashboard binds to `127.0.0.1` with public sharing disabled. No workflow automatically sends email.

## Historical credential exposure

An earlier version of the exploratory notebook contained a hard-coded OpenAI API key and SMTP app password. They have been removed from the current notebook, along with stored outputs. **Removing a value from the current files does not revoke it or remove it from Git history.** The account owner must revoke/rotate those credentials with the respective providers and review usage. Do not restore, test or reuse historical secrets. Repository-history cleanup, if needed, is a separate coordinated operation.

## Handling sensitive data

- Keep secrets in environment variables or an appropriate secrets manager. `.env` and runtime outputs are ignored by Git; the application does not auto-load `.env`.
- Review notebook source and outputs before committing. Avoid publishing private plant data, generated reports or vector-store contents without authorization.
- Enabling AI sends PDF text, the question, retrieved snippets and summary analytics to the configured OpenAI service. Only use data approved for that transfer.
- Treat retrieved PDF content as untrusted evidence. Generated recommendations and page citations need human review; the model has no authority to operate plant equipment.
- A local demo is not an authenticated hosted service. Add appropriate access controls and deployment review before making it public.

## Reporting an issue

If GitHub private vulnerability reporting is enabled, use the repository's Security tab. Otherwise contact the maintainer privately through a contact method they have published before sending sensitive details. Do not post live credentials, private data or exploit details in a public issue. There is no stated response-time guarantee or formal supported-release policy.
