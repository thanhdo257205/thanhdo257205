# Profile star card

The star total is fetched from GitHub's public repository API for the profile owner. It sums stars received by owned, public, non-fork repositories, including all API pages. This is different from the profile's Stars tab, which lists repositories the account has starred.

`Update profile stars` runs every six hours, at minute 17 UTC. It also runs when its code changes, and can be started from **Actions → Update profile stars → Run workflow**.

The workflow updates only `assets/stars.svg`, using the original design. Its timestamp is displayed in GMT+7. It uses the repository's built-in `GITHUB_TOKEN`; no personal access token or third-party badge service is needed. API or template failures keep the previous good image and fail the run.

The image is refreshed periodically, rather than on every page view. GitHub's image cache and scheduled-job queues can delay visibility. GitHub may disable schedules on a public repository after 60 days without activity; the Actions page allows re-enabling them.

For local use:

```sh
python3 -m unittest discover -s scripts -p 'test_*.py' -v
python3 scripts/update_stars.py --owner thanhdo257205
```
