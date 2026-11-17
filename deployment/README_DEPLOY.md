# VaultShare demo deployment (Render + Supabase + Cloudflare R2)

This is a deployment candidate, not a verified production security release.

## Before deploying
- Use a **private** R2 bucket. Create scoped S3-compatible object read/write/delete credentials for that bucket.
- Create a Supabase Postgres database. Obtain a compatible **SQLAlchemy/psycopg2** connection URI (typically `postgresql://...`). Supabase direct IPv6-only connections may require a session pooler with IPv4 support. Do not use transaction pooling without validating application behavior.
- Generate a NEW 32-byte base64 encryption key and NEW session secret. Do not reuse keys posted in chats or logs.
- Never upload local SQLite databases, `.env`, or user files.
- Check current free plan restrictions; some providers may require a payment method.

## Render service
1. New > Web Service > Connect your GitHub repository, branch `deployment`.
2. Runtime: Docker. Dockerfile path: `./Dockerfile`.
3. Set environment variables:
   - `ENV=production`
   - `DATABASE_URL=postgresql://...` (private)
   - `FILE_ENCRYPTION_KEY_B64=...` (private)
   - `SESSION_SECRET=...` (private)
   - `R2_ENDPOINT_URL=https://<account-id>.r2.cloudflarestorage.com`
   - `R2_ACCESS_KEY_ID=...` (private)
   - `R2_SECRET_ACCESS_KEY=...` (private)
   - `R2_BUCKET=...` (private bucket)
4. Deploy. Render's HTTPS URL serves frontend and backend on the SAME origin.
5. Test `/health`, `/docs`, `/register`, login, upload, integrity, download, sharing, logout.
6. Verify that an uploaded test file still downloads after a service redeploy.

## Important limitations
- Render free web services can sleep; first load can be slow.
- Free tiers and payment-method requirements can change. Verify in each dashboard.
- Do not invite real students or upload private documents until a security review.
- The existing 15 MB upload limit may exceed some provider's request handling limits; test at increasing sizes.
- This deployment intentionally starts with an EMPTY production database and storage.
- The application has no dedicated CSRF token or rate limiting; keep demo accounts synthetic.
- R2 encrypted files are stored privately, but permissions and bucket policy must be audited.
- Changing FILE_ENCRYPTION_KEY_B64 later prevents decrypting existing files unless a migration is performed.
