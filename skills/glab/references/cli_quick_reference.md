# glab Quick Reference Guide

A condensed reference for the most commonly used GitLab CLI commands.

## Authentication

```bash
glab auth login                    # Interactive login
echo "token" | glab auth login --stdin  # Login with token

# Diagnostics only after an auth/host error, or when explicitly requested
glab auth status
```

Notes:
- Stored `glab` auth is sufficient for most commands.
- `GITLAB_TOKEN`, `GITLAB_ACCESS_TOKEN`, and `OAUTH_TOKEN` override stored credentials when set.
- Do not run `glab auth status` as routine preflight. Use it for operator diagnostics, not brittle text parsing.

## Merge Requests

```bash
# Listing
glab mr list                       # All open MRs
glab mr list --assignee=@me        # MRs assigned to me
glab mr list --reviewer=@me        # MRs for me to review

# Creating
glab mr create                     # Interactive creation
glab mr create --title "Fix" --description "Desc"
glab mr create --title "Fix" --description "Closes #123"
glab mr create --draft             # Create draft MR
glab mr create --reviewer=alice,bob

# Viewing & Managing
glab mr view 123                   # View MR #123
glab mr checkout 123               # Checkout MR branch
glab mr approve 123                # Approve MR
glab mr merge 123                  # Merge MR
glab mr note create 123 -m "Comment"  # Add comment
glab mr note resolve 3107030349    # Resolve MR discussion by note or discussion ID
glab mr note reopen 3107030349     # Reopen MR discussion by note or discussion ID
```

Notes:
- If the MR body already contains `Closes #123`, avoid mixing that with `glab mr create --related-issue` unless you want `glab` to mutate the result. Verify afterward with `glab mr view`.
- Prefer exact-SHA merges for non-trivial delivery: `glab mr merge 123 --sha <head_sha> --remove-source-branch --yes`
- `No pipeline running` during merge can still end in a successful merge; verify the final MR state instead of treating that line as failure.

## Issues

```bash
# Listing
glab issue list                    # Open issues
glab issue list --all              # Open and closed issues
glab issue list --closed           # Closed issues
glab issue list --assignee=@me     # Assigned to me
glab issue list --label=bug        # With label

# `--opened` still appears in examples but prints a deprecation warning into stdout;
# omit it for open issues, especially when using `--output json`.

# Creating & Managing
glab issue create                  # Interactive
glab issue create --title "Bug" --label=bug
glab issue view 456                # View issue
glab issue close 456               # Close issue
glab issue update 456 --unlabel=todo
```

After MR auto-close:
- Re-check both issue state and labels: `glab issue view 456`
- If labels lag behind state, fix them explicitly: `glab issue update 456 --unlabel=doing --label=done`

## CI/CD

```bash
# Pipelines
glab ci view                       # Watch pipeline
glab ci list                       # List pipelines
glab ci list --ref main            # List pipelines for a ref / branch
glab ci list --ref main --per-page 5
glab ci status                     # Pipeline status
glab ci trace                      # View logs

# Wrong for `ci list`: --branch, --limit

# Running & Managing
glab ci run                        # Trigger pipeline
glab ci lint                       # Lint .gitlab-ci.yml
glab ci retry <job-id|job-name>    # Retry failed job
glab ci cancel pipeline <id>       # Cancel pipeline
```

## Repository

```bash
glab repo clone org/project        # Clone repository
glab repo view                     # View repo details
glab repo fork                     # Fork repository
```

## API

```bash
glab api projects/:id/merge_requests           # GET request
glab api --method POST projects/:id/issues \
  --field title="Bug"              # POST with data
```

## Common Flags

```bash
--repo, -R owner/repo              # Specify repository
--web, -w                          # Open in browser
--output, -o json                  # JSON output
--verbose                          # Verbose output
```

## Environment Variables

```bash
GITLAB_TOKEN=xxx                   # API token
GITLAB_HOST=gitlab.example.org     # Self-hosted GitLab
```

## Configuration

```bash
glab config get                    # View configuration
glab config set key value          # Set config value
```

## Complete Command List

- `glab alias` - Create command shortcuts
- `glab api` - Make API calls
- `glab auth` - Authentication management
- `glab changelog` - Generate changelogs
- `glab check-update` - Check for updates
- `glab ci` - CI/CD operations
- `glab cluster` - Kubernetes cluster management
- `glab completion` - Shell completion
- `glab config` - Configuration management
- `glab deploy-key` - Deploy key management
- `glab duo` - GitLab Duo AI features
- `glab gpg-key` - GPG key management
- `glab incident` - Incident management
- `glab issue` - Issue tracking
- `glab iteration` - Iteration management
- `glab job` - CI job operations
- `glab label` - Label management
- `glab mcp` - MCP server operations
- `glab milestone` - Milestone management
- `glab mr` - Merge request operations
- `glab opentofu` - OpenTofu integration
- `glab release` - Release management
- `glab repo` - Repository operations
- `glab runner` - Runner management
- `glab runner-controller` - Runner controller management
- `glab schedule` - Pipeline schedule management
- `glab securefile` - Secure file management
- `glab snippet` - Snippet operations
- `glab ssh-key` - SSH key management
- `glab stack` - Stack management
- `glab token` - Access token management
- `glab user` - User operations
- `glab variable` - CI/CD variable management
- `glab version` - Show version
- `glab work-items` - Work item management

## Tips

1. Use the known command patterns first; do not run help as preflight
2. Commands auto-detect repository context from git remote
3. Use `-R owner/repo` when outside a repository
4. Most commands have `--web` flag to open in browser
5. Use `--output=json` for scripting
6. If a flag fails, inspect that exact subcommand help once instead of guessing adjacent flags
