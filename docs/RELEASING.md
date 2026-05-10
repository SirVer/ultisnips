# Releasing UltiSnips

Maintainer notes for cutting a new release.

## Steps

1. **Update the ChangeLog.**
   - Rename the `next:` header to `version <X.Y> (DD-Mon-YYYY)`.
   - Add entries for every user-visible change since the previous release.
     Find the cut-off with `git log -1 --format=%h -- ChangeLog`, then
     `git log <last>..HEAD` to enumerate commits.
   - Open a PR for the ChangeLog and merge it before tagging.

2. **Tag and push.**

   ```
   git checkout master && git pull
   git tag -a <X.Y> -m "UltiSnips <X.Y>"
   git push origin <X.Y>
   ```

3. **Create a GitHub Release from the tag.**
   - GitHub UI: Releases → "Draft a new release" → choose the tag. This
     automatically attaches the right files to the release.
   - Title: `UltiSnips <X.Y>`.
   - Notes: paste the `version <X.Y>` section from `ChangeLog`. GitHub is picky
     about markdown, so you need to do some manual editing.

4. **Build the slim vim.org archive.**

   The GitHub source zip exceeds vim.org's upload limit because of the
   demo GIFs under `doc/`. Strip them with:

   ```
   ./scripts/slim-release.py <X.Y>
   ```

   This downloads the GitHub source zip for the tag, removes all GIFs,
   and writes `ultisnips-<X.Y>-vim.zip` in the current directory.

5. **Upload `ultisnips-<X.Y>-vim.zip` to vim.org.**

   https://www.vim.org/scripts/script.php?script_id=2715 → "upload new
   version". Paste the same release notes used for the GitHub Release.

   > **Note (2026-05-10, 4.0):** vim.org's upload form returned
   > "Request Entity Too Large" for every file (even 1 KB), across
   > multiple browsers and incognito sessions. The slim zip is fine —
   > the upload endpoint itself appears broken. 4.0 was therefore
   > **not** uploaded to vim.org. Retry on the next release; if the
   > form is still broken, contact vim.org admins.
